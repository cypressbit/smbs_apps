"""
Appointments: services people can book, the staff who give them, when each one works, and the bookings.
Times are stored in UTC and worked out in the business's timezone (SchedulerSettings.timezone).
Money is integer cents in the business's currency (USD for now).
"""
import hashlib
import secrets
import zoneinfo

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from smbs_apps.smbs_base.models import SettingsModel, SiteModel, TimestampModel


def timezone_choices():
    """Every IANA timezone, for the settings form (a callable, so migrations don't snapshot the list)."""
    return [(name, name.replace('_', ' ')) for name in sorted(zoneinfo.available_timezones())
            if '/' in name and not name.startswith(('Etc/', 'SystemV/', 'US/'))]


class CurrentSite(models.Model):
    """Fills in the site on save when it wasn't set (one site per installation in most hosts)."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.site_id:
            self.site_id = settings.SITE_ID
        super().save(*args, **kwargs)


class SchedulerSettings(CurrentSite, SettingsModel):
    timezone = models.CharField(max_length=64, default='America/Chicago', choices=timezone_choices,
                                help_text=_('Times on the booking page are in this timezone.'))
    slot_step_minutes = models.PositiveSmallIntegerField(
        default=30, choices=[(15, _('Every 15 minutes')), (30, _('Every 30 minutes')), (60, _('Every hour'))],
        help_text=_('How often a booking can start.'))
    min_notice_hours = models.PositiveSmallIntegerField(
        default=2, help_text=_('The earliest a booking can start, in hours from now.'))
    max_advance_days = models.PositiveSmallIntegerField(
        default=60, help_text=_('How far ahead people can book, in days.'))
    cancel_hours = models.PositiveSmallIntegerField(
        default=24, help_text=_('Customers can cancel online up to this many hours before. 0: any time before.'))
    intro = models.TextField(blank=True, help_text=_('A few words at the top of the booking page.'))

    class Meta:
        verbose_name = verbose_name_plural = _('scheduler settings')

    @classmethod
    def load(cls):
        """The settings, created with the defaults the first time."""
        found = cls.get_object()
        return found or cls.objects.create(site_id=settings.SITE_ID)

    @property
    def tz(self):
        try:
            return zoneinfo.ZoneInfo(self.timezone)
        except (zoneinfo.ZoneInfoNotFoundError, ValueError):
            return zoneinfo.ZoneInfo('UTC')


class StaffMember(CurrentSite, SiteModel, TimestampModel):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, help_text=_('Where this person hears about their bookings.'))
    bio = models.CharField(max_length=300, blank=True)
    photo_url = models.URLField(max_length=500, blank=True)
    active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    # A secret for this person's feed of bookings (subscribe to it from a calendar app).
    feed_token = models.CharField(max_length=64, unique=True, editable=False)

    class Meta:
        ordering = ['order', 'name', 'pk']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.feed_token:
            self.feed_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def new_feed_token(self):
        """A new feed address: the old one stops working (e.g. it was shared by mistake)."""
        self.feed_token = secrets.token_urlsafe(32)
        self.save(update_fields=['feed_token', 'updated'])


class Service(CurrentSite, SiteModel, TimestampModel):
    FREE, DEPOSIT, FULL = 'free', 'deposit', 'full'
    PAYMENTS = [(FREE, _('Free to book')), (DEPOSIT, _('Deposit when booking')),
                (FULL, _('Paid in full when booking'))]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    buffer_minutes = models.PositiveSmallIntegerField(
        default=0, help_text=_('Free time kept after each booking (travel, cleaning up).'))
    price_cents = models.PositiveIntegerField(default=0, help_text=_('0: no price shown.'))
    payment = models.CharField(max_length=8, choices=PAYMENTS, default=FREE)
    deposit_cents = models.PositiveIntegerField(default=0)
    staff = models.ManyToManyField(StaffMember, related_name='services', blank=True)
    active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name', 'pk']

    def __str__(self):
        return self.name

    def clean(self):
        if not 5 <= self.duration_minutes <= 12 * 60:
            raise ValidationError({'duration_minutes': _('Between 5 minutes and 12 hours.')})
        if self.payment == self.DEPOSIT and not 0 < self.deposit_cents <= max(self.price_cents, 0):
            raise ValidationError({'deposit_cents': _('A deposit above zero and no more than the price.')})
        if self.payment == self.FULL and self.price_cents < 50:
            raise ValidationError({'price_cents': _('A price of at least $0.50 to take payment.')})

    @property
    def amount_due_cents(self):
        """What the customer pays when booking."""
        return {self.DEPOSIT: self.deposit_cents, self.FULL: self.price_cents}.get(self.payment, 0)


class WeeklyHours(models.Model):
    """One range of working time on one day of the week (several per day for a break)."""
    DAYS = [(0, _('Monday')), (1, _('Tuesday')), (2, _('Wednesday')), (3, _('Thursday')), (4, _('Friday')),
            (5, _('Saturday')), (6, _('Sunday'))]

    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='hours')
    weekday = models.PositiveSmallIntegerField(choices=DAYS)
    start = models.TimeField()
    end = models.TimeField()

    class Meta:
        ordering = ['weekday', 'start']
        verbose_name_plural = 'weekly hours'

    def clean(self):
        if self.end <= self.start:
            raise ValidationError(_('The end must be after the start.'))


class TimeOff(models.Model):
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='time_off')
    start = models.DateTimeField()
    end = models.DateTimeField()
    note = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['start']
        verbose_name_plural = 'time off'

    def clean(self):
        if self.end <= self.start:
            raise ValidationError(_('The end must be after the start.'))


class ExternalCalendar(models.Model):
    """A calendar the staff member keeps elsewhere (Google, Outlook, Apple), read through its iCal address."""
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='calendars')
    label = models.CharField(max_length=60, blank=True)
    url = models.URLField(max_length=1000, help_text=_('The calendar’s private (secret) address in iCal format.'))
    busy = models.JSONField(default=list, blank=True)  # [[start ISO, end ISO], ...] in UTC, from the last read
    fetched_at = models.DateTimeField(null=True, blank=True)
    error = models.CharField(max_length=300, blank=True)
    error_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return self.label or self.masked_url

    @property
    def masked_url(self):
        """Enough to recognise the address, never enough to use it."""
        from urllib.parse import urlsplit
        host = urlsplit(self.url).hostname or ''
        return f'{host}/…{self.url[-4:]}' if self.url else ''


def _new_reference():
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # no 0/O, 1/I
    return 'B-' + ''.join(secrets.choice(alphabet) for _ in range(6))


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


class Booking(CurrentSite, SiteModel, TimestampModel):
    PENDING_PAYMENT, CONFIRMED, CANCELLED, EXPIRED = 'pending_payment', 'confirmed', 'cancelled', 'expired'
    STATUSES = [(PENDING_PAYMENT, _('Waiting for payment')), (CONFIRMED, _('Confirmed')),
                (CANCELLED, _('Cancelled')), (EXPIRED, _('Not paid in time'))]
    HOLDING = (PENDING_PAYMENT, CONFIRMED)  # statuses that keep the time taken

    reference = models.CharField(max_length=12, unique=True, default=_new_reference, editable=False)
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='bookings')
    staff = models.ForeignKey(StaffMember, on_delete=models.PROTECT, related_name='bookings')
    start = models.DateTimeField(db_index=True)
    end = models.DateTimeField()
    busy_until = models.DateTimeField(help_text='The end plus the service’s buffer: when the next booking may start.')
    status = models.CharField(max_length=16, choices=STATUSES, default=CONFIRMED, db_index=True)
    hold_until = models.DateTimeField(null=True, blank=True, help_text='A booking waiting for payment holds its '
                                      'time until then.')
    # What the service was when booked (it may change later).
    service_name = models.CharField(max_length=100)
    price_cents = models.PositiveIntegerField(default=0)
    amount_due_cents = models.PositiveIntegerField(default=0)
    amount_paid_cents = models.PositiveIntegerField(default=0)
    amount_refunded_cents = models.PositiveIntegerField(default=0)
    payment_ref = models.CharField(max_length=255, blank=True)  # e.g. the Stripe Checkout session
    # The customer.
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    note = models.TextField(blank=True, max_length=1000)
    cancel_token_hash = models.CharField(max_length=64, blank=True, db_index=True, editable=False)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.CharField(max_length=16, blank=True)  # customer | owner
    no_show = models.BooleanField(default=False)

    class Meta:
        ordering = ['start']
        indexes = [models.Index(fields=['staff', 'start'])]

    def __str__(self):
        return f'{self.reference} {self.service_name} {self.start:%Y-%m-%d %H:%M}'

    def new_cancel_token(self):
        """A token for the customer's cancel link; only its hash is stored. Call before saving."""
        token = secrets.token_urlsafe(24)
        self.cancel_token_hash = hash_token(token)
        return token
