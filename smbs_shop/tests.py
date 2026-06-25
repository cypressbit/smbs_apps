from decimal import Decimal

from django.test import TestCase
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.utils import timezone

from smbs_apps.smbs_shop.models import (
    ShopSettings,
    ShopCategory,
    ShopItem,
    ShopItemReview,
    ShopCart,
    ShopCartItem,
    ShopOrder,
    ShopOrderItem,
    ShopPayment,
)


class ShopSettingsTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_create_settings(self):
        s = ShopSettings.objects.create(site=self.site)
        self.assertFalse(s.enable_paypal)
        self.assertFalse(s.enable_stripe)

    def test_get_settings_returns_object(self):
        s = ShopSettings.objects.create(site=self.site)
        self.assertEqual(ShopSettings.get_settings(), s)

    def test_paypal_mode_default_sandbox(self):
        s = ShopSettings.objects.create(site=self.site)
        self.assertEqual(s.paypal_mode, 'sandbox')


class ShopCategoryTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(username='vendor', password='pass')

    def test_create_category(self):
        cat = ShopCategory.objects.create(
            site=self.site,
            user=self.user,
            slug='apparel',
            title='Apparel',
            description='Clothing items',
        )
        self.assertEqual(cat.title, 'Apparel')


class ShopItemTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(username='vendor', password='pass')

    def _make_item(self, **kwargs):
        defaults = dict(
            site=self.site,
            user=self.user,
            slug='shirt',
            title='Blue Shirt',
            description='A nice shirt',
            language='en',
            publish_date=timezone.now(),
            price=Decimal('29.99'),
        )
        defaults.update(kwargs)
        return ShopItem(**defaults)

    def test_get_effective_price_without_discount(self):
        item = self._make_item(price=Decimal('50.00'), discount_price=None)
        self.assertEqual(item.get_effective_price(), Decimal('50.00'))

    def test_get_effective_price_with_discount(self):
        item = self._make_item(price=Decimal('50.00'), discount_price=Decimal('35.00'))
        self.assertEqual(item.get_effective_price(), Decimal('35.00'))

    def test_generate_sku_format(self):
        item = self._make_item()
        sku = item.generate_sku()
        self.assertIn('-', sku)
        self.assertTrue(sku.isupper() or '-' in sku)

    def test_sku_truncated_to_reasonable_length(self):
        item = self._make_item(title='A Very Long Product Title That Exceeds Limits')
        sku = item.generate_sku()
        parts = sku.split('-')
        self.assertLessEqual(len(parts[0]), 10)

    def test_is_in_stock_default(self):
        item = self._make_item()
        self.assertTrue(item.is_in_stock)

    def test_is_featured_default_false(self):
        item = self._make_item()
        self.assertFalse(item.is_featured)

    def test_get_absolute_url(self):
        item = self._make_item()
        url = item.get_absolute_url()
        self.assertIn('shirt', url)


class ShopCartTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='pass')

    def test_create_cart(self):
        cart = ShopCart.objects.create(user=self.user)
        self.assertEqual(cart.user, self.user)
        self.assertEqual(cart.items.count(), 0)

    def test_one_cart_per_user(self):
        ShopCart.objects.create(user=self.user)
        with self.assertRaises(Exception):
            ShopCart.objects.create(user=self.user)


class ShopOrderTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='pass')

    def test_create_order(self):
        order = ShopOrder.objects.create(
            user=self.user,
            total_price=Decimal('99.99'),
            status='pending',
        )
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_price, Decimal('99.99'))

    def test_order_status_choices(self):
        statuses = ['pending', 'completed', 'in_payment']
        for status in statuses:
            order = ShopOrder.objects.create(
                user=self.user,
                total_price=Decimal('10.00'),
                status=status,
            )
            self.assertEqual(order.status, status)


class ShopPaymentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='pass')
        self.order = ShopOrder.objects.create(
            user=self.user,
            total_price=Decimal('49.99'),
            status='in_payment',
        )

    def test_create_payment(self):
        payment = ShopPayment.objects.create(
            order=self.order,
            amount=Decimal('49.99'),
            payment_method='stripe',
            payment_status='pending',
        )
        self.assertEqual(payment.payment_method, 'stripe')
        self.assertEqual(payment.payment_status, 'pending')

    def test_payment_completed(self):
        payment = ShopPayment.objects.create(
            order=self.order,
            amount=Decimal('49.99'),
            payment_method='paypal',
            payment_status='completed',
        )
        self.assertEqual(payment.payment_status, 'completed')
