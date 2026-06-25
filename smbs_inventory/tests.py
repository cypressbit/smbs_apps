from django.test import TestCase
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.utils import timezone

from smbs_apps.smbs_inventory.models import InventorySettings, Category, Item, ItemReview


class InventorySettingsTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_create_settings(self):
        s = InventorySettings.objects.create(site=self.site)
        self.assertEqual(s.navigation_title, 'Products')
        self.assertEqual(s.navigation_slug, 'products')

    def test_get_object_none_when_missing(self):
        self.assertIsNone(InventorySettings.get_object())

    def test_get_settings_returns_object(self):
        s = InventorySettings.objects.create(site=self.site)
        self.assertEqual(InventorySettings.get_settings(), s)


class CategoryTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(username='vendor', password='pass')

    def test_create_category(self):
        cat = Category.objects.create(
            site=self.site,
            user=self.user,
            slug='electronics',
            title='Electronics',
            description='Electronic goods',
        )
        self.assertEqual(cat.title, 'Electronics')
        self.assertEqual(cat.slug, 'electronics')


class ItemTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(username='vendor', password='pass')
        self.category = Category.objects.create(
            site=self.site,
            user=self.user,
            slug='gadgets',
            title='Gadgets',
            description='Cool gadgets',
        )

    def _make_item(self, **kwargs):
        defaults = dict(
            site=self.site,
            user=self.user,
            slug='test-item',
            title='Test Item',
            description='A test item',
            language='en',
            publish_date=timezone.now(),
        )
        defaults.update(kwargs)
        return Item.objects.create(**defaults)

    def test_create_item(self):
        item = self._make_item()
        self.assertEqual(item.title, 'Test Item')
        self.assertTrue(item.in_stock)
        self.assertTrue(item.is_visible)
        self.assertFalse(item.is_featured)

    def test_get_absolute_url(self):
        item = self._make_item()
        url = item.get_absolute_url()
        self.assertIn('test-item', url)

    def test_in_stock_default_true(self):
        item = self._make_item()
        self.assertTrue(item.in_stock)

    def test_available_items_default(self):
        item = self._make_item()
        self.assertEqual(item.available_items, 1)


class ItemReviewTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(username='reviewer', password='pass')
        self.vendor = User.objects.create_user(username='vendor', password='pass')
        self.item = Item.objects.create(
            site=self.site,
            user=self.vendor,
            slug='reviewed-item',
            title='Reviewed Item',
            description='Item for reviews',
            language='en',
            publish_date=timezone.now(),
        )

    def test_create_positive_review(self):
        review = ItemReview.objects.create(
            user=self.user,
            inventory_item=self.item,
            positive_review=True,
            comment='Great product!',
        )
        self.assertTrue(review.positive_review)
        self.assertEqual(review.comment, 'Great product!')

    def test_create_negative_review(self):
        review = ItemReview.objects.create(
            user=self.user,
            inventory_item=self.item,
            positive_review=False,
            comment='Disappointed.',
        )
        self.assertFalse(review.positive_review)
