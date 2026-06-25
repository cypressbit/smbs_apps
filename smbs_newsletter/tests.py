from django.test import TestCase
from django.contrib.sites.models import Site
from django.contrib.auth.models import User

from smbs_apps.smbs_newsletter.models import NewsletterSettings, NewsletterOptIn


class NewsletterSettingsTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_create_settings(self):
        s = NewsletterSettings.objects.create(site=self.site)
        self.assertEqual(s.backend, NewsletterSettings.MAILCHIMP)

    def test_get_object_none_when_missing(self):
        self.assertIsNone(NewsletterSettings.get_object())

    def test_get_object_returns_settings(self):
        s = NewsletterSettings.objects.create(site=self.site)
        self.assertEqual(NewsletterSettings.get_object(), s)

    def test_mailchimp_is_only_backend_choice(self):
        choices = [b[0] for b in NewsletterSettings.BACKEND_CHOICES]
        self.assertIn(NewsletterSettings.MAILCHIMP, choices)


class NewsletterOptInTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(username='subscriber', password='pass')

    def test_create_opt_in(self):
        opt_in = NewsletterOptIn.objects.create(
            site=self.site,
            user=self.user,
            terms='I agree to receive newsletters.',
        )
        self.assertEqual(opt_in.user, self.user)
        self.assertEqual(opt_in.terms, 'I agree to receive newsletters.')

    def test_timestamps_set(self):
        opt_in = NewsletterOptIn.objects.create(
            site=self.site,
            user=self.user,
            terms='Terms text.',
        )
        self.assertIsNotNone(opt_in.created)
