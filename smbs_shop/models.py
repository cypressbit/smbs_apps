from taggit.managers import TaggableManager

from django.utils.translation import gettext_lazy as _
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

from smbs_apps.smbs_base.models import SiteModel, TimestampModel, ObjectMetadata, SettingsModel


class ShopSettings(SettingsModel):
    navigation_title = models.CharField(max_length=32, default=_('Products'))
    navigation_slug = models.CharField(max_length=32, default=_('products'))
    page_title = models.CharField(max_length=64, default=_('Product list'))

    enable_paypal = models.BooleanField(default=False)
    paypal_client_id = models.CharField(max_length=255, blank=True, null=True)
    paypal_client_secret = models.CharField(max_length=255, blank=True, null=True)
    paypal_mode = models.CharField(max_length=10, choices=[('sandbox', 'Sandbox'), ('live', 'Live')], default='sandbox')
    paypal_webhook_id = models.CharField(max_length=255, blank=True, null=True)

    enable_stripe = models.BooleanField(default=False)
    stripe_api_key = models.CharField(max_length=255, blank=True, null=True)
    stripe_webhook_secret = models.CharField(max_length=255, blank=True, null=True)

    @classmethod
    def get_settings(cls):
        return cls.get_object()

    class Meta:
        verbose_name = _('Shop Settings')


class Category(SiteModel, TimestampModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='shop_categories')
    slug = models.SlugField(max_length=255, unique=True)
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')


class Item(SiteModel, TimestampModel):
    class LanguageChoices(models.TextChoices):
        ENGLISH = 'en', _('English')
        FRENCH = 'fr', _('French')
        SPANISH = 'es', _('Spanish')

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='shop_items')
    slug = models.SlugField(max_length=255, unique=True)
    metadata = models.ForeignKey(ObjectMetadata, on_delete=models.SET_NULL, blank=True, null=True, related_name='shop_items')
    language = models.CharField(max_length=10, choices=LanguageChoices.choices)
    publish_date = models.DateTimeField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True, related_name='items')
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    cover_image = models.ImageField(upload_to='smbs_shop_images', blank=True, null=True)
    tags = TaggableManager(related_name='shop_items')
    stock_quantity = models.PositiveSmallIntegerField(default=1)
    is_in_stock = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sku = models.CharField(max_length=64, unique=True)

    def get_absolute_url(self):
        return reverse('shop:item_detail', args=[self.slug])

    def get_related_items(self):
        objects = self.tags.similar_objects()
        return [o for o in objects if isinstance(o, Item)]

    def get_effective_price(self):
        return self.discount_price if self.discount_price else self.price

    class Meta:
        ordering = ['-publish_date']
        verbose_name = _('Item')
        verbose_name_plural = _('Items')


class ItemReview(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shop_item_reviews')
    inventory_item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='reviews')
    positive_review = models.BooleanField(default=True)
    comment = models.TextField()

    class Meta:
        verbose_name = _('Item Review')
        verbose_name_plural = _('Item Reviews')


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shop_cart')
    items = models.ManyToManyField(Item, through='CartItem')

    class Meta:
        verbose_name = _('Cart')
        verbose_name_plural = _('Carts')


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = _('Cart Item')
        verbose_name_plural = _('Cart Items')


class Order(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shop_orders')
    items = models.ManyToManyField(Item, through='OrderItem')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed')])

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')


class Payment(TimestampModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed')])

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')