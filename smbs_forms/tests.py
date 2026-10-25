import requests
from django.test import Client, TestCase, override_settings
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


class TurnstileContactTest(TestCase):
    """With Turnstile keys, the form needs a valid token instead of a CSRF token."""
    VALID = ContactViewTest.VALID

    def setUp(self):
        from django.urls import NoReverseMatch, reverse
        try:
            self.URL = reverse('smbs_forms:contact')
        except NoReverseMatch:
            self.skipTest('smbs_forms URLs are not routed in this project')
        self.client = Client(enforce_csrf_checks=True)

    def test_csrf_is_still_required_without_turnstile(self):
        self.assertEqual(self.client.post(self.URL, self.VALID).status_code, 403)
        self.assertEqual(Contact.objects.count(), 0)

    @override_settings(TURNSTILE_SITE_KEY='site', TURNSTILE_SECRET_KEY='secret')
    def test_turnstile_replaces_csrf(self):
        from unittest import mock
        verified = mock.Mock(**{'json.return_value': {'success': True}})
        with mock.patch('smbs_apps.smbs_forms.turnstile.requests.post', return_value=verified) as post:
            response = self.client.post(self.URL, {**self.VALID, 'cf-turnstile-response': 'token'})
        self.assertRedirects(response, '/?contact=sent#contact', fetch_redirect_response=False)
        self.assertEqual(post.call_args.kwargs['data']['response'], 'token')
        self.assertEqual(Contact.objects.count(), 1)

    @override_settings(TURNSTILE_SITE_KEY='site', TURNSTILE_SECRET_KEY='secret')
    def test_missing_or_rejected_tokens_fail(self):
        from unittest import mock
        rejected = mock.Mock(**{'json.return_value': {'success': False}})
        with mock.patch('smbs_apps.smbs_forms.turnstile.requests.post', return_value=rejected):
            self.client.post(self.URL, self.VALID)
            self.client.post(self.URL, {**self.VALID, 'cf-turnstile-response': 'bad'})
        with mock.patch('smbs_apps.smbs_forms.turnstile.requests.post', side_effect=requests.ConnectionError):
            self.client.post(self.URL, {**self.VALID, 'cf-turnstile-response': 'token'})
        self.assertEqual(Contact.objects.count(), 0)

    @override_settings(TURNSTILE_SITE_KEY='site-key-1', TURNSTILE_SECRET_KEY='secret')
    def test_widget_renders_turnstile_without_a_csrf_token(self):
        from smbs_apps.smbs_pages import rendering
        doc = {'schema_version': 1, 'sections': [{'id': 's_1', 'style': {}, 'rows': [{'id': 'r_1', 'style': {}, 'columns': [
            {'id': 'c_1', 'span': {'xs': 12}, 'valign': 'top', 'widgets': [{'id': 'w_1', 'type': 'contact_form', 'props': {}}]}]}]}]}
        html = str(rendering.render_document(doc))
        self.assertIn('data-sitekey="site-key-1"', html)
        self.assertNotIn('csrfmiddlewaretoken', html)
