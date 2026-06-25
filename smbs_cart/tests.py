from decimal import Decimal

from django.test import TestCase
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.utils import timezone

from smbs_apps.smbs_cart.models import CartSettings, Cart, Order
from smbs_apps.smbs_inventory.models import Category, Item


class CartSettingsTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_create_settings(self):
        s = CartSettings.objects.create(site=self.site)
        self.assertEqual(s.payment_provider, CartSettings.PAYPAL)

    def test_get_object_none_when_missing(self):
        self.assertIsNone(CartSettings.get_object())

    def test_get_settings_returns_object(self):
        s = CartSettings.objects.create(site=self.site)
        self.assertEqual(CartSettings.get_settings(), s)

    def test_paypal_is_provider_choice(self):
        providers = [p[0] for p in CartSettings.PROVIDERS]
        self.assertIn(CartSettings.PAYPAL, providers)


class CartTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(username='shopper', password='pass')

    def test_create_cart(self):
        cart = Cart.objects.create(site=self.site, user=self.user)
        self.assertEqual(cart.user, self.user)
        self.assertEqual(cart.items.count(), 0)

    def test_cart_without_user(self):
        cart = Cart.objects.create(site=self.site)
        self.assertIsNone(cart.user)


class OrderTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(username='buyer', password='pass')
        self.cart = Cart.objects.create(site=self.site, user=self.user)

    def test_create_order(self):
        order = Order.objects.create(
            user=self.user,
            cart=self.cart,
            description='Order for 2 items',
            total=Decimal('59.98'),
            receipt_id='RCPT-001',
        )
        self.assertEqual(order.total, Decimal('59.98'))
        self.assertEqual(order.receipt_id, 'RCPT-001')

    def test_order_uuid_auto_generated(self):
        order = Order.objects.create(
            user=self.user,
            cart=self.cart,
            description='Test order',
            total=Decimal('10.00'),
            receipt_id='RCPT-002',
        )
        self.assertIsNotNone(order.order_id)

    def test_order_uuid_unique_per_order(self):
        order1 = Order.objects.create(
            user=self.user, cart=self.cart,
            description='Order 1', total=Decimal('10.00'), receipt_id='R1'
        )
        order2 = Order.objects.create(
            user=self.user, cart=self.cart,
            description='Order 2', total=Decimal('20.00'), receipt_id='R2'
        )
        self.assertNotEqual(order1.order_id, order2.order_id)
