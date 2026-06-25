from django.test import TestCase
from django.contrib.sites.models import Site
from django.contrib.auth.models import User

from smbs_apps.smbs_profile.models import ProfileSettings, LocationProfile, ImageProfile
from smbs_apps.smbs_cities_light.models import Country, State, City


class ProfileSettingsTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_create_settings(self):
        s = ProfileSettings.objects.create(site=self.site)
        self.assertEqual(s.user_profile, ProfileSettings.LOCATION)

    def test_get_object_none_when_missing(self):
        self.assertIsNone(ProfileSettings.get_object())

    def test_get_object_returns_settings(self):
        s = ProfileSettings.objects.create(site=self.site)
        self.assertEqual(ProfileSettings.get_object(), s)

    def test_location_is_valid_choice(self):
        choices = [c[0] for c in ProfileSettings.PROFILE_CHOICES]
        self.assertIn(ProfileSettings.LOCATION, choices)


class LocationProfileTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='profuser', password='pass')
        country = Country.objects.create(
            name='United States', code='US', slug='united-states'
        )
        state = State.objects.create(
            country=country, name='Texas', slug='texas'
        )
        self.city = City.objects.create(
            state=state, name='Austin', slug='austin'
        )

    def test_create_profile_without_city(self):
        profile = LocationProfile.objects.create(
            user=self.user,
            newsletter_signup=False,
        )
        self.assertEqual(profile.user, self.user)
        self.assertIsNone(profile.city)

    def test_create_profile_with_city(self):
        profile = LocationProfile.objects.create(
            user=self.user,
            city=self.city,
        )
        self.assertEqual(profile.city, self.city)

    def test_newsletter_signup_default_false(self):
        profile = LocationProfile.objects.create(user=self.user)
        self.assertFalse(profile.newsletter_signup)

    def test_one_profile_per_user(self):
        LocationProfile.objects.create(user=self.user)
        with self.assertRaises(Exception):
            LocationProfile.objects.create(user=self.user)
