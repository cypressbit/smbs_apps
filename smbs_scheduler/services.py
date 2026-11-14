"""
The scheduler's public API: free times, booking (and the payment hold), confirming, cancelling.

The host decides what happens around a booking (payment, emails) through the signals below:
- `booking_confirmed(booking)`: a booking is confirmed (booked free, or its payment arrived);
- `booking_cancelled(booking, by)`: cancelled by the customer or the owner;
- `booking_expired(booking)`: a booking waiting for payment wasn't paid in time.
They're sent once the database transaction commits.
"""
import datetime as dt
import logging

from django.db import transaction
from django.dispatch import Signal
from django.utils import timezone
from django.utils.translation import gettext as _

from smbs_apps.smbs_scheduler import availability, ical
from smbs_apps.smbs_scheduler.models import (Booking, ExternalCalendar, SchedulerSettings, Service, StaffMember,
                                             hash_token)

logger = logging.getLogger(__name__)

booking_confirmed = Signal()
booking_cancelled = Signal()
booking_expired = Signal()

CALENDAR_MAX_AGE = dt.timedelta(minutes=10)      # busy times older than this are read again for the slots
CALENDAR_MAX_AGE_BOOKING = dt.timedelta(minutes=2)  # and again, fresher, just before booking
CALENDAR_RETRY_AFTER_ERROR = dt.timedelta(minutes=5)
HOLD_MINUTES = 35  # a booking waiting for payment keeps its time this long (a Stripe Checkout lasts 30 at least)
MAX_DAYS_PER_QUERY = 42


class SchedulerError(Exception):
    """A booking we can't make or change; the message is for the customer."""


def _send(signal, booking, **kwargs):
    transaction.on_commit(lambda: signal.send(sender=Booking, booking=booking, **kwargs))


# --------------------------------------------------------------------------
# What can be booked
# --------------------------------------------------------------------------

def bookable_services():
    """Active services that at least one active staff member offers."""
    return list(Service.objects.filter(active=True, staff__active=True).distinct().prefetch_related('staff'))


def staff_for(service):
    return list(service.staff.filter(active=True).order_by('order', 'name', 'pk'))


def refresh_calendar(calendar, max_age=CALENDAR_MAX_AGE, now=None):
    """Reads the calendar again if its busy times are older than max_age. Never raises: a failure keeps the
    last busy times and records the error for the owner."""
    now = now or timezone.now()
    if calendar.fetched_at and now - calendar.fetched_at < max_age:
        return calendar
    if calendar.error_at and now - calendar.error_at < CALENDAR_RETRY_AFTER_ERROR and \
            (not calendar.fetched_at or calendar.error_at > calendar.fetched_at):
        return calendar
    try:
        text = ical.fetch(calendar.url)
        busy = ical.busy_intervals(text, SchedulerSettings.load().tz, start=now - dt.timedelta(days=1))
    except ical.CalendarError as exc:
        ExternalCalendar.objects.filter(pk=calendar.pk).update(error=str(exc)[:300], error_at=now)
        calendar.error, calendar.error_at = str(exc)[:300], now
        return calendar
    except Exception:
        logger.exception('Reading external calendar %s failed', calendar.pk)
        ExternalCalendar.objects.filter(pk=calendar.pk).update(error=_('Reading the calendar failed.'), error_at=now)
        return calendar
    calendar.busy = [[first.isoformat(), last.isoformat()] for first, last in busy]
    calendar.fetched_at, calendar.error, calendar.error_at = now, '', None
    ExternalCalendar.objects.filter(pk=calendar.pk).update(busy=calendar.busy, fetched_at=now, error='',
                                                           error_at=None)
    return calendar


def refresh_calendars(staff_members, max_age=CALENDAR_MAX_AGE):
    for staff in staff_members:
        for calendar in staff.calendars.all():
            refresh_calendar(calendar, max_age)


def check_calendar(url):
    """Reads a calendar address the owner is adding: (normalised url, how many busy times ahead). Raises
    CalendarError with a message for the owner."""
    url = ical.normalise_url(url)
    busy = ical.busy_intervals(ical.fetch(url), SchedulerSettings.load().tz)
    return url, len(busy)


def free_times(service, staff=None, first_day=None, last_day=None, *, now=None):
    """
    {start (UTC): [staff, ...]} for `service` with `staff` (None: anyone who offers it), business dates
    first_day to last_day (default: the next 14 days, at most MAX_DAYS_PER_QUERY).
    """
    settings = SchedulerSettings.load()
    now = now or timezone.now()
    today = now.astimezone(settings.tz).date()
    first_day = max(first_day or today, today)
    last_day = min(last_day or first_day + dt.timedelta(days=13), first_day + dt.timedelta(days=MAX_DAYS_PER_QUERY - 1),
                   today + dt.timedelta(days=settings.max_advance_days))
    if last_day < first_day:
        return {}
    candidates = staff_for(service)
    if staff is not None:
        candidates = [member for member in candidates if member.pk == staff.pk]
    refresh_calendars(candidates)
    return availability.slots(service, candidates, first_day, last_day, settings=settings, now=now)


# --------------------------------------------------------------------------
# Booking
# --------------------------------------------------------------------------

def book(service, start, *, name, email, phone='', note='', staff=None, now=None):
    """
    Books `service` at `start` (aware) with `staff`, or with the first free person when None. Returns
    (booking, cancel_token). Free services are confirmed at once; others wait for payment (`hold_until`),
    and the host sends the customer to pay. Raises SchedulerError when the time isn't free (any more).
    """
    now = now or timezone.now()
    if not service.active:
        raise SchedulerError(_('This service can’t be booked right now.'))
    if start.tzinfo is None:
        raise SchedulerError(_('Choose a time.'))
    name, email = (name or '').strip()[:100], (email or '').strip()[:254]
    if not name or not email:
        raise SchedulerError(_('Please give your name and email.'))
    candidates = staff_for(service)
    if staff is not None:
        candidates = [member for member in candidates if member.pk == staff.pk]
    if not candidates:
        raise SchedulerError(_('Nobody offers this service right now.'))
    # Fresh busy times from their own calendars, read before taking the lock (a network call).
    refresh_calendars(candidates, max_age=CALENDAR_MAX_AGE_BOOKING)
    settings = SchedulerSettings.load()
    day = start.astimezone(settings.tz).date()
    with transaction.atomic():
        # One booking at a time per person: lock their rows (always in the same order, no deadlocks).
        locked = list(StaffMember.objects.select_for_update().filter(pk__in=[m.pk for m in candidates])
                      .order_by('pk'))
        by_pk = {member.pk: member for member in locked}
        chosen = next((by_pk[member.pk] for member in candidates
                       if start in availability.staff_slots(service, by_pk[member.pk], day, day,
                                                            settings=settings, now=now)), None)
        if chosen is None:
            raise SchedulerError(_('That time was just taken. Please choose another.'))
        due = service.amount_due_cents
        booking = Booking(
            service=service, staff=chosen, start=start, end=start + dt.timedelta(minutes=service.duration_minutes),
            busy_until=start + dt.timedelta(minutes=service.duration_minutes + service.buffer_minutes),
            status=Booking.PENDING_PAYMENT if due else Booking.CONFIRMED,
            hold_until=now + dt.timedelta(minutes=HOLD_MINUTES) if due else None,
            service_name=service.name, price_cents=service.price_cents, amount_due_cents=due,
            name=name, email=email, phone=(phone or '').strip()[:40], note=(note or '').strip()[:1000])
        token = booking.new_cancel_token()
        booking.save()
        if booking.status == Booking.CONFIRMED:
            _send(booking_confirmed, booking)
    return booking, token


def find(reference):
    return Booking.objects.select_related('service', 'staff').filter(reference=reference).first()


def find_by_token(token):
    if not token:
        return None
    return Booking.objects.select_related('service', 'staff').filter(cancel_token_hash=hash_token(token)).first()


@transaction.atomic
def paid(booking, *, amount_paid_cents, payment_ref='', now=None):
    """
    The payment for a booking arrived. Returns True when the booking is confirmed (or already was). A payment
    that arrives after the hold ended for a time someone else has taken since returns False: the booking stays
    expired with the payment recorded, and the owner must refund it.
    """
    now = now or timezone.now()
    booking = Booking.objects.select_for_update().get(pk=booking.pk)
    booking.amount_paid_cents = max(booking.amount_paid_cents, amount_paid_cents)
    booking.payment_ref = payment_ref or booking.payment_ref
    if booking.status == Booking.CONFIRMED:
        booking.save(update_fields=['amount_paid_cents', 'payment_ref', 'updated'])
        return True
    if booking.status in (Booking.PENDING_PAYMENT, Booking.EXPIRED):
        StaffMember.objects.select_for_update().filter(pk=booking.staff_id).first()
        clash = availability.busy_for(booking.staff, booking.start, booking.busy_until, now=now,
                                      exclude_booking=booking)
        if booking.status == Booking.PENDING_PAYMENT or not any(
                first < booking.busy_until and last > booking.start for first, last in clash):
            booking.status, booking.hold_until = Booking.CONFIRMED, None
            booking.save(update_fields=['status', 'hold_until', 'amount_paid_cents', 'payment_ref', 'updated'])
            _send(booking_confirmed, booking)
            return True
    booking.save(update_fields=['amount_paid_cents', 'payment_ref', 'updated'])
    return False


@transaction.atomic
def expire(booking):
    """A booking's payment didn't happen (the checkout expired): its time is free again."""
    booking = Booking.objects.select_for_update().get(pk=booking.pk)
    if booking.status != Booking.PENDING_PAYMENT:
        return booking
    booking.status, booking.hold_until = Booking.EXPIRED, None
    booking.save(update_fields=['status', 'hold_until', 'updated'])
    _send(booking_expired, booking)
    return booking


def expire_unpaid(now=None):
    """Expires every booking whose payment hold has passed (in case the payment provider never said)."""
    now = now or timezone.now()
    stale = Booking.objects.filter(status=Booking.PENDING_PAYMENT, hold_until__lt=now - dt.timedelta(minutes=5))
    return [expire(booking) for booking in stale]


def can_cancel(booking, now=None):
    """Whether the customer may still cancel online."""
    now = now or timezone.now()
    if booking.status not in Booking.HOLDING or booking.start <= now:
        return False
    hours = SchedulerSettings.load().cancel_hours
    return booking.start - now >= dt.timedelta(hours=hours)


@transaction.atomic
def cancel(booking, *, by, now=None):
    """Cancels a booking: by='customer' (within the cancellation window) or 'owner' (any time)."""
    now = now or timezone.now()
    booking = Booking.objects.select_for_update().select_related('service', 'staff').get(pk=booking.pk)
    if booking.status not in Booking.HOLDING:
        raise SchedulerError(_('This booking is already cancelled.'))
    if by == 'customer' and not can_cancel(booking, now):
        raise SchedulerError(_('It’s too late to cancel online. Please contact the business.'))
    booking.status, booking.hold_until = Booking.CANCELLED, None
    booking.cancelled_at, booking.cancelled_by = now, by
    booking.save(update_fields=['status', 'hold_until', 'cancelled_at', 'cancelled_by', 'updated'])
    _send(booking_cancelled, booking, by=by)
    return booking


def refunded(booking, amount_refunded_cents):
    Booking.objects.filter(pk=booking.pk, amount_refunded_cents__lt=amount_refunded_cents).update(
        amount_refunded_cents=amount_refunded_cents, updated=timezone.now())


def upcoming(staff=None, *, now=None):
    """Bookings that hold time from now on (for the panel and the feed)."""
    now = now or timezone.now()
    found = Booking.objects.select_related('service', 'staff').filter(status__in=Booking.HOLDING, end__gte=now)
    return found.filter(staff=staff) if staff is not None else found


def feed_for(token):
    """(staff, .ics text) for a staff member's private feed: their bookings from 30 days ago on."""
    staff = StaffMember.objects.filter(feed_token=token).first() if token else None
    if staff is None:
        return None, None
    since = timezone.now() - dt.timedelta(days=30)
    bookings = staff.bookings.select_related('staff').filter(status=Booking.CONFIRMED, end__gte=since)
    return staff, ical.feed(staff, bookings, name=staff.name)
