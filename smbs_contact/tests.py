from django.test import TestCase
from django.contrib.sites.models import Site

from smbs_apps.smbs_contact.models import ContactSettings


class ContactSettingsTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_create_settings(self):
        s = ContactSettings.objects.create(site=self.site)
        self.assertIsNone(s.display_name)
        self.assertIsNone(s.phone_number)
        self.assertIsNone(s.email_address)

    def test_get_object_returns_none_when_missing(self):
        self.assertIsNone(ContactSettings.get_object())

    def test_get_object_returns_settings(self):
        s = ContactSettings.objects.create(site=self.site)
        self.assertEqual(ContactSettings.get_object(), s)

    def test_settings_with_values(self):
        s = ContactSettings.objects.create(
            site=self.site,
            display_name='Acme Corp',
            phone_number='555-1234',
            email_address='info@acme.com',
        )
        self.assertEqual(s.display_name, 'Acme Corp')
        self.assertEqual(s.email_address, 'info@acme.com')
