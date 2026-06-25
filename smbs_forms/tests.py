from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.sites.models import Site

from smbs_apps.smbs_forms.validators import validate_phone
from smbs_apps.smbs_forms.models import (
    ContactFormSettings,
    Contact,
    ContactWithAddressFormSettings,
    ContactWithAddress,
)


class ValidatePhoneTest(TestCase):
    def test_digits_only_passes(self):
        result = validate_phone('5551234567')
        self.assertEqual(result, 5551234567)

    def test_formatted_phone_passes(self):
        result = validate_phone('(555) 123-4567')
        self.assertIsNotNone(result)

    def test_phone_with_dashes_passes(self):
        validate_phone('555-123-4567')

    def test_letters_raise_validation_error(self):
        with self.assertRaises(ValidationError):
            validate_phone('abc-defg')

    def test_empty_letters_raise(self):
        with self.assertRaises(ValidationError):
            validate_phone('555-CALL-NOW')


class ContactFormSettingsTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_create_settings(self):
        s = ContactFormSettings.objects.create(site=self.site)
        self.assertFalse(s.email_enabled)

    def test_get_object_none_when_missing(self):
        self.assertIsNone(ContactFormSettings.get_object())

    def test_get_settings_returns_defaults(self):
        settings = ContactFormSettings.get_settings()
        self.assertFalse(settings['email_enabled'])
        self.assertEqual(settings['success_url'], '/')


class ContactModelTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_create_contact(self):
        contact = Contact(
            site=self.site,
            name='John Doe',
            email='john@example.com',
            phone='5551234567',
            message='Hello there.',
        )
        contact.clean()
        contact.save()
        self.assertEqual(contact.name, 'John Doe')

    def test_invalid_phone_raises(self):
        from django.core.exceptions import ValidationError as DjValidationError
        contact = Contact(
            site=self.site,
            name='Jane',
            email='jane@example.com',
            phone='not-a-phone',
            message='Hi.',
        )
        with self.assertRaises(DjValidationError):
            contact.full_clean()


class ContactWithAddressTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_create_contact_with_address(self):
        c = ContactWithAddress(
            site=self.site,
            name='Alice',
            email='alice@example.com',
            phone='5559876543',
            address='123 Main St',
            city='Springfield',
            state='IL',
            message='Need info.',
        )
        c.clean()
        c.save()
        self.assertEqual(c.address, '123 Main St')
        self.assertEqual(c.city, 'Springfield')
