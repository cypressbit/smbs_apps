"""
When a service can start: each staff member's weekly hours on each day (in the business's timezone, so
daylight saving moves with the clock), minus their time off, their bookings (with buffers) and the busy times
of their own calendars, from the minimum notice to the booking horizon.

Everything here is read-only and works on what it's given or reads from the database; refreshing external
calendars happens in services.
"""
import datetime as dt

from django.utils import timezone

from smbs_apps.smbs_scheduler.ical import merge
from smbs_apps.smbs_scheduler.models import Booking, SchedulerSettings


def _parse(value):
    parsed = dt.datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


def busy_for(staff, start, end, *, now=None, exclude_booking=None):
    """[(start, end)] UTC when `staff` can't take a booking between start and end."""
    now = now or timezone.now()
    busy = []
    bookings = Booking.objects.filter(staff=staff, status__in=Booking.HOLDING, start__lt=end, busy_until__gt=start)
    if exclude_booking is not None:
        bookings = bookings.exclude(pk=exclude_booking.pk)
    for booking in bookings:
        if booking.status == Booking.PENDING_PAYMENT and booking.hold_until and booking.hold_until <= now:
            continue  # its payment window has passed: the time is free again
        busy.append((booking.start, booking.busy_until))
    busy += [(off.start, off.end) for off in staff.time_off.filter(start__lt=end, end__gt=start)]
    for calendar in staff.calendars.all():
        for first, last in calendar.busy or []:
            first, last = _parse(first), _parse(last)
            if first < end and last > start:
                busy.append((first, last))
    return merge(busy)


def _overlaps(first, last, busy):
    return any(first < b_end and last > b_start for b_start, b_end in busy)


def _windows(staff, day, tz, hours_by_day):
    for hours in hours_by_day.get(day.weekday(), []):
        first = dt.datetime.combine(day, hours.start, tzinfo=tz)
        last = dt.datetime.combine(day, hours.end, tzinfo=tz)
        # Round trip through UTC: a time that doesn't exist (the hour skipped in spring) moves forward.
        yield first.astimezone(dt.timezone.utc), last.astimezone(dt.timezone.utc)


def staff_slots(service, staff, first_day, last_day, *, settings=None, now=None, busy=None):
    """The UTC start times `staff` can give `service` from first_day to last_day (business dates, inclusive)."""
    settings = settings or SchedulerSettings.load()
    now = now or timezone.now()
    tz = settings.tz
    step = dt.timedelta(minutes=settings.slot_step_minutes)
    length = dt.timedelta(minutes=service.duration_minutes)
    taken = length + dt.timedelta(minutes=service.buffer_minutes)
    earliest = now + dt.timedelta(hours=settings.min_notice_hours)
    latest = now + dt.timedelta(days=settings.max_advance_days)
    range_start = dt.datetime.combine(first_day, dt.time(), tzinfo=tz).astimezone(dt.timezone.utc)
    range_end = dt.datetime.combine(last_day + dt.timedelta(days=1), dt.time(), tzinfo=tz).astimezone(dt.timezone.utc)
    if busy is None:
        busy = busy_for(staff, range_start, range_end + taken, now=now)
    hours_by_day = {}
    for hours in staff.hours.all():
        hours_by_day.setdefault(hours.weekday, []).append(hours)
    slots = []
    day = first_day
    while day <= last_day:
        midnight = dt.datetime.combine(day, dt.time(), tzinfo=tz)
        for window_start, window_end in _windows(staff, day, tz, hours_by_day):
            # Starts line up with the step from local midnight (9:00, 9:30…), whatever the hours' minutes.
            offset = (window_start.astimezone(tz).replace(tzinfo=None) - midnight.replace(tzinfo=None))
            steps = -(-offset // step)  # ceiling
            start = (midnight.replace(tzinfo=None) + steps * step).replace(tzinfo=tz).astimezone(dt.timezone.utc)
            while start + length <= window_end:
                if earliest <= start <= latest and not _overlaps(start, start + taken, busy):
                    slots.append(start)
                start += step
        day += dt.timedelta(days=1)
    return sorted(set(slots))


def slots(service, staff_members, first_day, last_day, *, settings=None, now=None):
    """
    {start (UTC): [staff, ...]}: who can give `service` at each start time from first_day to last_day, in
    the staff members' order (the first is who "Anyone available" gets).
    """
    settings = settings or SchedulerSettings.load()
    now = now or timezone.now()
    found = {}
    for staff in staff_members:
        for start in staff_slots(service, staff, first_day, last_day, settings=settings, now=now):
            found.setdefault(start, []).append(staff)
    return dict(sorted(found.items()))
