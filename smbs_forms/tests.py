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


class ContactViewTest(TestCase):

    def setUp(self):
        from django.urls import NoReverseMatch, reverse
        try:
            self.URL = reverse('smbs_forms:contact')
        except NoReverseMatch:
            self.skipTest('smbs_forms URLs are not routed in this project')
    VALID = {'name': 'Rosa', 'email': 'rosa@example.com', 'phone': '(555) 123-4567', 'message': 'Hi'}

    def test_get_redirects_home(self):
        response = self.client.get(self.URL)
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_valid_post_returns_to_the_page_with_a_notice(self):
        response = self.client.post(self.URL, self.VALID, HTTP_REFERER='http://testserver/contact-us/?a=1')
        self.assertRedirects(response, '/contact-us/?a=1&contact=sent#contact', fetch_redirect_response=False)
        self.assertEqual(Contact.objects.count(), 1)

    def test_invalid_post_returns_with_error(self):
        response = self.client.post(self.URL, {**self.VALID, 'email': 'nope'}, HTTP_REFERER='http://testserver/x/')
        self.assertRedirects(response, '/x/?contact=error#contact', fetch_redirect_response=False)
        self.assertEqual(Contact.objects.count(), 0)

    def test_foreign_referer_is_ignored(self):
        response = self.client.post(self.URL, self.VALID, HTTP_REFERER='https://evil.example/')
        self.assertRedirects(response, '/?contact=sent#contact', fetch_redirect_response=False)

    def test_configured_success_url_wins(self):
        ContactFormSettings.objects.create(site=Site.objects.get_current(), success_url='https://example.com/thanks')
        response = self.client.post(self.URL, self.VALID)
        self.assertRedirects(response, 'https://example.com/thanks', fetch_redirect_response=False)
