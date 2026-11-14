import datetime as dt
import zoneinfo
from unittest import mock

from django.test import TestCase

from smbs_apps.smbs_scheduler import availability, ical, services
from smbs_apps.smbs_scheduler.models import (Booking, ExternalCalendar, SchedulerSettings, Service, StaffMember,
                                             TimeOff, WeeklyHours)

CHICAGO = zoneinfo.ZoneInfo('America/Chicago')
UTC = dt.timezone.utc


def local(year, month, day, hour, minute=0):
    return dt.datetime(year, month, day, hour, minute, tzinfo=CHICAGO)


# Monday 16 November 2026, 7:00 in Chicago.
NOW = local(2026, 11, 16, 7)
MONDAY = dt.date(2026, 11, 16)


def times(slots):
    return [start.astimezone(CHICAGO).strftime('%a %H:%M') for start in slots]


class SchedulerTestCase(TestCase):

    def setUp(self):
        self.settings = SchedulerSettings.load()
        self.settings.timezone = 'America/Chicago'
        self.settings.slot_step_minutes = 30
        self.settings.min_notice_hours = 2
        self.settings.max_advance_days = 60
        self.settings.cancel_hours = 24
        self.settings.save()
        self.ana = self.staff('Ana')
        self.ben = self.staff('Ben', order=1)
        self.session = Service.objects.create(name='Portrait session', duration_minutes=60)
        self.session.staff.add(self.ana, self.ben)

    def staff(self, name, order=0, hours=((0, 9, 12),)):
        member = StaffMember.objects.create(name=name, email=f'{name.lower()}@example.com', order=order)
        for weekday, start, end in hours:
            WeeklyHours.objects.create(staff=member, weekday=weekday, start=dt.time(start), end=dt.time(end))
        return member

    def slots(self, staff, service=None, day=MONDAY, last=None):
        return availability.staff_slots(service or self.session, staff, day, last or day, now=NOW)


class AvailabilityTests(SchedulerTestCase):

    def test_hours_step_and_notice(self):
        # 9–12, one hour long: 9:00 is inside the 2 hours' notice from 7:00, so 9:00 is the first (7+2=9).
        self.assertEqual(times(self.slots(self.ana)), ['Mon 09:00', 'Mon 09:30', 'Mon 10:00', 'Mon 10:30', 'Mon 11:00'])
        self.settings.min_notice_hours = 3
        self.settings.save()
        self.assertEqual(times(self.slots(self.ana))[0], 'Mon 10:00')

    def test_starts_line_up_with_the_step(self):
        WeeklyHours.objects.filter(staff=self.ana).update(start=dt.time(9, 15))
        self.assertEqual(times(self.slots(self.ana))[:2], ['Mon 09:30', 'Mon 10:00'])

    def test_a_break_and_the_horizon(self):
        WeeklyHours.objects.create(staff=self.ana, weekday=0, start=dt.time(13), end=dt.time(14))
        self.assertIn('Mon 13:00', times(self.slots(self.ana)))
        self.assertNotIn('Mon 12:00', times(self.slots(self.ana)))
        self.settings.max_advance_days = 3
        self.settings.save()
        self.assertEqual(self.slots(self.ana, day=MONDAY + dt.timedelta(days=7)), [])

    def test_daylight_saving(self):
        # Clocks go forward on Sunday 14 March 2027 in Chicago: 9:00 is 15:00 UTC before and 14:00 UTC after.
        WeeklyHours.objects.create(staff=self.ana, weekday=6, start=dt.time(9), end=dt.time(10))
        self.settings.max_advance_days = 200
        self.settings.save()
        before = self.slots(self.ana, day=dt.date(2027, 3, 7))
        after = self.slots(self.ana, day=dt.date(2027, 3, 14))
        self.assertEqual([s.astimezone(UTC).hour for s in before], [15])
        self.assertEqual([s.astimezone(UTC).hour for s in after], [14])

    def test_bookings_with_buffer_and_held_payments(self):
        self.session.buffer_minutes = 30
        self.session.save()
        start = local(2026, 11, 16, 10)
        Booking.objects.create(service=self.session, staff=self.ana, start=start, end=start + dt.timedelta(hours=1),
                               busy_until=start + dt.timedelta(minutes=90), service_name='x', name='C', email='c@x.co')
        # 10:00–11:00 plus 30 minutes: 9:00 would run into it with its own buffer (9:00–10:30); 11:30 is free.
        self.assertEqual(self.slots(self.ana), [])  # and 11:30 would end after 12:00
        WeeklyHours.objects.filter(staff=self.ana).update(end=dt.time(14))
        self.assertEqual(times(self.slots(self.ana)), ['Mon 11:30', 'Mon 12:00', 'Mon 12:30', 'Mon 13:00'])
        # A booking waiting for payment holds its time only until its hold ends.
        Booking.objects.all().update(status=Booking.PENDING_PAYMENT, hold_until=NOW + dt.timedelta(minutes=5))
        self.assertNotIn('Mon 10:00', times(self.slots(self.ana)))
        Booking.objects.all().update(hold_until=NOW - dt.timedelta(minutes=1))
        self.assertIn('Mon 10:00', times(self.slots(self.ana)))
        Booking.objects.all().update(status=Booking.CANCELLED)
        self.assertIn('Mon 10:00', times(self.slots(self.ana)))

    def test_time_off(self):
        TimeOff.objects.create(staff=self.ana, start=local(2026, 11, 16, 10), end=local(2026, 11, 16, 11))
        self.assertEqual(times(self.slots(self.ana)), ['Mon 09:00', 'Mon 11:00'])

    def test_anyone_lists_who_is_free_in_order(self):
        TimeOff.objects.create(staff=self.ana, start=local(2026, 11, 16, 9), end=local(2026, 11, 16, 10))
        found = availability.slots(self.session, [self.ana, self.ben], MONDAY, MONDAY, now=NOW)
        self.assertEqual([m.name for m in found[local(2026, 11, 16, 9).astimezone(UTC)]], ['Ben'])
        self.assertEqual([m.name for m in found[local(2026, 11, 16, 10).astimezone(UTC)]], ['Ana', 'Ben'])


CALENDAR = '''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Google Inc//Google Calendar 70.9054//EN
BEGIN:VEVENT
UID:weekly@google.com
DTSTART;TZID=America/Chicago:20261109T100000
DTEND;TZID=America/Chicago:20261109T103000
RRULE:FREQ=WEEKLY;BYDAY=MO
SUMMARY:Dentist (private)
END:VEVENT
BEGIN:VEVENT
UID:free@google.com
DTSTART:20261116T170000Z
DTEND:20261116T180000Z
TRANSP:TRANSPARENT
SUMMARY:Shown as free
END:VEVENT
BEGIN:VEVENT
UID:cancelled@google.com
DTSTART:20261116T160000Z
DTEND:20261116T170000Z
STATUS:CANCELLED
END:VEVENT
BEGIN:VEVENT
UID:allday@google.com
DTSTART;VALUE=DATE:20261123
DTEND;VALUE=DATE:20261124
SUMMARY:Holiday
END:VEVENT
END:VCALENDAR
'''


class CalendarTests(SchedulerTestCase):

    def test_busy_times(self):
        busy = ical.busy_intervals(CALENDAR, CHICAGO, start=NOW, end=NOW + dt.timedelta(days=15))
        self.assertEqual([(a.astimezone(CHICAGO).strftime('%m-%d %H:%M'), b.astimezone(CHICAGO).strftime('%m-%d %H:%M'))
                          for a, b in busy],
                         [('11-16 10:00', '11-16 10:30'),    # the weekly event, repeated; free and cancelled skipped
                          ('11-23 00:00', '11-24 00:00'),    # the all-day event, in the business's timezone
                          ('11-30 10:00', '11-30 10:30')])

    def test_a_connected_calendar_blocks_slots(self):
        ExternalCalendar.objects.create(staff=self.ana, url='https://calendar.google.com/calendar/ical/x/basic.ics')
        with mock.patch('smbs_apps.smbs_scheduler.ical.fetch', return_value=CALENDAR), \
                mock.patch('django.utils.timezone.now', return_value=NOW):
            found = services.free_times(self.session, self.ana, MONDAY, MONDAY + dt.timedelta(days=7), now=NOW)
        mondays = times(s for s in found if s.astimezone(CHICAGO).date() == MONDAY)
        self.assertEqual(mondays, ['Mon 09:00', 'Mon 10:30', 'Mon 11:00'])  # 9:30 and 10:00 overlap 10:00–10:30
        self.assertFalse([s for s in found if s.astimezone(CHICAGO).date() == dt.date(2026, 11, 23)])

    def test_a_failing_calendar_keeps_its_last_busy_times(self):
        calendar = ExternalCalendar.objects.create(
            staff=self.ana, url='https://calendar.google.com/x.ics', fetched_at=NOW - dt.timedelta(hours=1),
            busy=[[local(2026, 11, 16, 9).isoformat(), local(2026, 11, 16, 12).isoformat()]])
        with mock.patch('smbs_apps.smbs_scheduler.ical.fetch', side_effect=ical.CalendarError('It refused.')):
            services.refresh_calendar(calendar, now=NOW)
        calendar.refresh_from_db()
        self.assertEqual(calendar.error, 'It refused.')
        self.assertEqual(self.slots(self.ana), [])
        # It isn't asked again for a few minutes.
        with mock.patch('smbs_apps.smbs_scheduler.ical.fetch') as fetch:
            services.refresh_calendar(calendar, now=NOW + dt.timedelta(minutes=1))
        fetch.assert_not_called()

    def test_addresses(self):
        self.assertEqual(ical.normalise_url('webcal://p01-caldav.icloud.com/published/2/abc'),
                         'https://p01-caldav.icloud.com/published/2/abc')
        for bad in ('http://calendar.google.com/x.ics', 'ftp://x.com/a.ics', 'https://user:pw@x.com/a.ics', 'x.ics'):
            with self.assertRaises(ical.CalendarError, msg=bad):
                ical.normalise_url(bad)
        for address in ('10.0.0.5', '127.0.0.1', '169.254.169.254', '::1'):
            with mock.patch('socket.getaddrinfo', return_value=[(None, None, None, '', (address, 443))]), \
                    mock.patch('requests.get') as get, self.assertRaises(ical.CalendarError, msg=address):
                ical.fetch('https://calendar.example.com/x.ics')
            get.assert_not_called()

    def test_redirects_are_checked_too(self):
        hop = mock.Mock(is_redirect=True, headers={'Location': 'https://internal.example/x.ics'})
        public = [(None, None, None, '', ('93.184.216.34', 443))]
        private = [(None, None, None, '', ('10.1.2.3', 443))]
        with mock.patch('socket.getaddrinfo', side_effect=[public, private]), \
                mock.patch('requests.get', return_value=hop), self.assertRaises(ical.CalendarError):
            ical.fetch('https://calendar.example.com/x.ics')


class BookingTests(SchedulerTestCase):

    def book(self, hour, staff=None, service=None, **kwargs):
        return services.book(service or self.session, local(2026, 11, 16, hour), staff=staff, name='Carla',
                             email='carla@example.com', now=NOW, **kwargs)

    def test_anyone_then_the_next_person_then_full(self):
        with self.captureOnCommitCallbacks(execute=True):
            first, token = self.book(10)
        second, _ = self.book(10)
        self.assertEqual((first.staff, second.staff), (self.ana, self.ben))
        self.assertEqual(first.status, Booking.CONFIRMED)
        self.assertEqual(services.find_by_token(token), first)
        self.assertEqual(len(first.cancel_token_hash), 64)
        with self.assertRaisesMessage(services.SchedulerError, 'just taken'):
            self.book(10)
        with self.assertRaisesMessage(services.SchedulerError, 'just taken'):  # not a start time at all
            services.book(self.session, local(2026, 11, 16, 10, 15), name='C', email='c@x.co', now=NOW)

    def test_a_chosen_person(self):
        booking, _ = self.book(11, staff=self.ben)
        self.assertEqual(booking.staff, self.ben)
        with self.assertRaises(services.SchedulerError):
            self.book(11, staff=self.ben)

    def test_paid_services_wait_for_payment(self):
        self.session.payment, self.session.price_cents, self.session.deposit_cents = Service.DEPOSIT, 25000, 5000
        self.session.save()
        received = []
        services.booking_confirmed.connect(lambda **kw: received.append(kw['booking'].reference), weak=False)
        booking, _ = self.book(10, staff=self.ana)
        self.assertEqual((booking.status, booking.amount_due_cents), (Booking.PENDING_PAYMENT, 5000))
        self.assertEqual(booking.hold_until, NOW + dt.timedelta(minutes=services.HOLD_MINUTES))
        with self.assertRaises(services.SchedulerError):
            self.book(10, staff=self.ana)  # held
        with self.captureOnCommitCallbacks(execute=True):
            self.assertTrue(services.paid(booking, amount_paid_cents=5000, payment_ref='cs_1', now=NOW))
        booking.refresh_from_db()
        self.assertEqual((booking.status, booking.amount_paid_cents, booking.hold_until),
                         (Booking.CONFIRMED, 5000, None))
        self.assertEqual(received, [booking.reference])
        self.assertTrue(services.paid(booking, amount_paid_cents=5000, now=NOW))  # a repeat changes nothing

    def test_unpaid_bookings_expire_and_late_payments_dont_double_book(self):
        self.session.payment, self.session.price_cents = Service.FULL, 9000
        self.session.save()
        booking, _ = self.book(10, staff=self.ana)
        services.expire(booking)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.EXPIRED)
        other, _ = self.book(10, staff=self.ana)  # the time is free again
        self.assertFalse(services.paid(booking, amount_paid_cents=9000, now=NOW))  # the owner must refund it
        booking.refresh_from_db()
        self.assertEqual((booking.status, booking.amount_paid_cents), (Booking.EXPIRED, 9000))
        later = NOW + dt.timedelta(minutes=services.HOLD_MINUTES + 10)
        self.assertEqual([b.pk for b in services.expire_unpaid(now=later)], [other.pk])

    def test_cancelling(self):
        booking, _ = self.book(10)
        with self.assertRaisesMessage(services.SchedulerError, 'too late'):
            services.cancel(booking, by='customer', now=NOW)  # 3 hours before, the window is 24
        early = NOW - dt.timedelta(days=2)
        with self.captureOnCommitCallbacks(execute=True):
            services.cancel(booking, by='customer', now=early)
        booking.refresh_from_db()
        self.assertEqual((booking.status, booking.cancelled_by), (Booking.CANCELLED, 'customer'))
        with self.assertRaises(services.SchedulerError):
            services.cancel(booking, by='owner', now=NOW)
        self.book(10, staff=booking.staff)  # free again

    def test_invite_and_feed(self):
        booking, _ = self.book(10, note='First time; bring the dog, please')
        text = ical.invite(booking, organizer_name='Studio', organizer_email='hi@studio.com',
                           url='https://studio.example.com/book/B-X/')
        self.assertIn('DTSTART:20261116T160000Z', text)
        self.assertIn('METHOD:PUBLISH', text)
        self.assertIn('bring the dog\\, please', text)
        self.assertTrue(all(len(line.encode()) <= 75 for line in text.split('\r\n')))
        self.assertIn('STATUS:CANCELLED', ical.invite(booking, cancelled=True))
        staff, feed = services.feed_for(booking.staff.feed_token)
        self.assertEqual(staff, booking.staff)
        self.assertIn(f'UID:{booking.reference}@', feed)
        self.assertEqual(services.feed_for('nope'), (None, None))
