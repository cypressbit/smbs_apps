"""
iCal both ways:
- reading a staff member's own calendar (its private iCal address) for the times they're busy;
- writing a booking as an invite (.ics) and a staff member's private feed of bookings.

Reading fetches an address the owner typed, so it refuses anything but public https hosts (no SSRF into
the cluster), caps the size and time, and never logs the address (it's a secret: whoever has it can read
the calendar).
"""
import datetime as dt
import ipaddress
import logging
import socket
from urllib.parse import urljoin, urlsplit

import requests
from django.utils import timezone

logger = logging.getLogger(__name__)

FETCH_TIMEOUT = 5          # seconds
MAX_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 3
LOOK_AHEAD_DAYS = 120      # busy times are read this far ahead
PRODID = '-//SMBS//Scheduler//EN'


class CalendarError(Exception):
    """A calendar address we can't read: the message is safe to show the owner (it never has the address)."""


def normalise_url(url):
    """webcal:// (Apple, Outlook) is https://. Raises CalendarError for anything that isn't an https address."""
    url = (url or '').strip()
    if url.lower().startswith('webcal://'):
        url = 'https://' + url[len('webcal://'):]
    parts = urlsplit(url)
    if parts.scheme.lower() != 'https' or not parts.hostname:
        raise CalendarError('Use the calendar’s https:// (or webcal://) address.')
    if parts.username or parts.password:
        raise CalendarError('That address has a user name or password in it; use the calendar’s secret address.')
    return url


def _check_host(host, port):
    """Raises CalendarError unless every address the host resolves to is public."""
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError):
        raise CalendarError('That calendar’s address doesn’t exist.')
    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        if not address.is_global or address.is_multicast:
            raise CalendarError('That address isn’t a public calendar.')


def fetch(url):
    """The calendar's text. Raises CalendarError (safe to show) for any failure."""
    url = normalise_url(url)
    for _ in range(MAX_REDIRECTS + 1):
        parts = urlsplit(url)
        _check_host(parts.hostname, parts.port or 443)
        try:
            response = requests.get(url, timeout=FETCH_TIMEOUT, stream=True, allow_redirects=False,
                                    headers={'Accept': 'text/calendar, */*;q=0.5', 'User-Agent': 'SMBS-Scheduler/1'})
        except requests.RequestException:
            raise CalendarError('The calendar didn’t answer. We’ll try again in a few minutes.')
        if response.is_redirect:
            url = normalise_url(urljoin(url, response.headers.get('Location', '')))
            response.close()
            continue
        if response.status_code in (401, 403, 404, 410):
            raise CalendarError('The calendar refused the address. Copy its secret iCal address again.')
        if response.status_code != 200:
            raise CalendarError(f'The calendar answered with an error ({response.status_code}).')
        body, size = [], 0
        for chunk in response.iter_content(64 * 1024):
            size += len(chunk)
            if size > MAX_BYTES:
                response.close()
                raise CalendarError('That calendar is too large to read (over 2 MB).')
            body.append(chunk)
        text = b''.join(body).decode(response.encoding or 'utf-8', errors='replace')
        if 'BEGIN:VCALENDAR' not in text[:2000].upper():
            raise CalendarError('That address isn’t an iCal calendar. Use the calendar’s iCal (.ics) address.')
        return text
    raise CalendarError('The calendar’s address redirects too many times.')


def _aware(value, tz):
    """An event time as an aware UTC datetime: dates are midnight in the business's timezone; floating times
    are in the business's timezone."""
    if isinstance(value, dt.datetime):
        aware = value if value.tzinfo else value.replace(tzinfo=tz)
    else:
        aware = dt.datetime.combine(value, dt.time(), tzinfo=tz)
    return aware.astimezone(dt.timezone.utc)


def busy_intervals(text, tz, start=None, end=None):
    """
    [(start, end)] in UTC when the calendar is busy between start and end (default: now to LOOK_AHEAD_DAYS):
    recurring events expanded; events marked free (TRANSP:TRANSPARENT) or cancelled are left out; all-day
    events block their whole days. Raises CalendarError if the text isn't a calendar.
    """
    import icalendar
    import recurring_ical_events
    start = start or timezone.now()
    end = end or start + dt.timedelta(days=LOOK_AHEAD_DAYS)
    try:
        calendar = icalendar.Calendar.from_ical(text)
        events = recurring_ical_events.of(calendar).between(start, end)
    except Exception as exc:  # the libraries raise many kinds of errors for broken files
        logger.info('Unreadable iCal calendar: %s', type(exc).__name__)
        raise CalendarError('We couldn’t read that calendar’s events.')
    busy = []
    for event in events:
        if str(event.get('TRANSP', '')).upper() == 'TRANSPARENT' or \
                str(event.get('STATUS', '')).upper() == 'CANCELLED':
            continue
        begins = event.get('DTSTART')
        if begins is None:
            continue
        ends = event.get('DTEND')
        first = _aware(begins.dt, tz)
        if ends is not None:
            last = _aware(ends.dt, tz)
        elif event.get('DURATION') is not None:
            last = first + event['DURATION'].dt
        else:  # no end: a date is one day, a time is a moment (RFC 5545)
            last = _aware(begins.dt + dt.timedelta(days=1), tz) if not isinstance(begins.dt, dt.datetime) else first
        if last > first:
            busy.append((first, last))
    return merge(busy)


def merge(intervals):
    """Sorted, with overlapping or touching intervals joined."""
    merged = []
    for first, last in sorted(intervals):
        if merged and first <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], last))
        else:
            merged.append((first, last))
    return merged


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------

def _escape(text):
    return (str(text or '').replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,')
            .replace('\r\n', '\\n').replace('\n', '\\n'))


def _stamp(value):
    return value.astimezone(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def _fold(line):
    """Lines longer than 75 octets continue on the next line, indented (RFC 5545 §3.1)."""
    raw = line.encode()
    if len(raw) <= 75:
        return line
    parts, current = [], b''
    for char in line:
        encoded = char.encode()
        if len(current) + len(encoded) > (75 if not parts else 74):
            parts.append(current.decode())
            current = b''
        current += encoded
    parts.append(current.decode())
    return '\r\n '.join(parts)


def _event(booking, *, organizer_name='', organizer_email='', url='', cancelled=False, sequence=0):
    host = urlsplit(url).hostname if url else 'smbs-scheduler'
    lines = [
        'BEGIN:VEVENT',
        f'UID:{booking.reference}@{host}',
        f'DTSTAMP:{_stamp(timezone.now())}',
        f'DTSTART:{_stamp(booking.start)}',
        f'DTEND:{_stamp(booking.end)}',
        f'SEQUENCE:{sequence}',
        f'SUMMARY:{_escape(f"{booking.service_name}: {booking.name}" if not organizer_name else booking.service_name)}',
        f'DESCRIPTION:{_escape(_description(booking))}',
        f'STATUS:{"CANCELLED" if cancelled else "CONFIRMED"}',
    ]
    if url:
        lines.append(f'URL:{url}')
    if organizer_email:
        lines.append(f'ORGANIZER;CN={_escape(organizer_name)}:mailto:{organizer_email}')
    lines.append('END:VEVENT')
    return lines


def _description(booking):
    parts = [f'{booking.service_name} with {booking.staff.name}', f'Booking {booking.reference}',
             f'{booking.name} <{booking.email}>']
    if booking.phone:
        parts.append(booking.phone)
    if booking.note:
        parts.append(booking.note)
    return '\n'.join(parts)


def _calendar(lines, method=None, name=None):
    head = ['BEGIN:VCALENDAR', 'VERSION:2.0', f'PRODID:{PRODID}', 'CALSCALE:GREGORIAN']
    if method:
        head.append(f'METHOD:{method}')
    if name:
        head.append(f'X-WR-CALNAME:{_escape(name)}')
    return '\r\n'.join(_fold(line) for line in head + lines + ['END:VCALENDAR']) + '\r\n'


def invite(booking, *, organizer_name='', organizer_email='', url='', cancelled=False):
    """One booking as an .ics file to attach to an email (METHOD:PUBLISH, or CANCEL when it was cancelled)."""
    return _calendar(_event(booking, organizer_name=organizer_name, organizer_email=organizer_email, url=url,
                            cancelled=cancelled, sequence=1 if cancelled else 0),
                     method='CANCEL' if cancelled else 'PUBLISH')


def feed(staff, bookings, name):
    """A staff member's bookings as a calendar to subscribe to."""
    lines = []
    for booking in bookings:
        lines += _event(booking)
    return _calendar(lines, name=name)
