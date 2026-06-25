from django.test import TestCase
from django.contrib.sites.models import Site

from smbs_apps.smbs_alerts.models import Alert


class AlertModelTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_create_default_alert(self):
        alert = Alert.objects.create(
            site=self.site,
            title='Test Alert',
            content='Some content',
        )
        self.assertEqual(alert.alert_type, Alert.SUCCESS)
        self.assertEqual(alert.position, Alert.TOP)
        self.assertFalse(alert.homepage_only)

    def test_all_alert_types_defined(self):
        types = [t[0] for t in Alert.ALERT_TYPES]
        self.assertIn(Alert.SUCCESS, types)
        self.assertIn(Alert.WARNING, types)
        self.assertIn(Alert.INFO, types)
        self.assertIn(Alert.DANGER, types)

    def test_both_position_choices_defined(self):
        positions = [p[0] for p in Alert.POSITIONS]
        self.assertIn(Alert.TOP, positions)
        self.assertIn(Alert.BOTTOM, positions)

    def test_homepage_only_flag(self):
        alert = Alert.objects.create(
            site=self.site,
            title='Home Alert',
            content='Home only',
            homepage_only=True,
        )
        self.assertTrue(alert.homepage_only)

    def test_danger_bottom_alert(self):
        alert = Alert.objects.create(
            site=self.site,
            title='Critical',
            content='System down',
            alert_type=Alert.DANGER,
            position=Alert.BOTTOM,
        )
        self.assertEqual(alert.alert_type, Alert.DANGER)
        self.assertEqual(alert.position, Alert.BOTTOM)

    def test_timestamps_auto_set(self):
        alert = Alert.objects.create(
            site=self.site, title='T', content='C'
        )
        self.assertIsNotNone(alert.created)
        self.assertIsNotNone(alert.updated)
