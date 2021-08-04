import uuid

from django.db import models
from django.contrib.auth.models import User

from smbs_base.models import SiteModel, TimestampModel, SettingsModel
from smbs_inventory.models import Item


class CartSettings(SettingsModel):
    PAYPAL = 'paypal'

    PROVIDERS = [
        (PAYPAL, 'PayPal'),
    ]

    payment_provider = models.CharField(max_length=32, choices=PROVIDERS, default=PAYPAL)

    @classmethod
    def get_settings(cls):
        cart_settings = cls.get_object()
        return cart_settings

    class Meta:
        verbose_name = 'Cart Settings'


class Cart(SiteModel, TimestampModel):
    # Non-editable fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    # Editable fields
    items = models.ManyToManyField(Item)


class Order(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    order_id = models.UUIDField(default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    description = models.TextField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_id = models.CharField(max_length=64)
