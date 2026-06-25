from django.test import TestCase
from django.contrib.sites.models import Site

from smbs_apps.smbs_social.models import SocialSettings


class SocialSettingsTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_create_settings(self):
        s = SocialSettings.objects.create(site=self.site)
        self.assertFalse(s.enable_fb_pages_popup)
        self.assertEqual(s.fb_pages_popup_delay, 10000)

    def test_get_object_returns_none_when_missing(self):
        self.assertIsNone(SocialSettings.get_object())

    def test_get_object_returns_settings(self):
        s = SocialSettings.objects.create(site=self.site)
        self.assertEqual(SocialSettings.get_object(), s)

    def test_fb_popup_enabled(self):
        s = SocialSettings.objects.create(
            site=self.site,
            enable_fb_pages_popup=True,
            fb_pages_script='<script></script>',
            fb_pages_popup_delay=5000,
        )
        self.assertTrue(s.enable_fb_pages_popup)
        self.assertEqual(s.fb_pages_popup_delay, 5000)
