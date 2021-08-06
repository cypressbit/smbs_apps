from taggit.managers import TaggableManager

from django.utils.translation import gettext_lazy as _

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

from smbs_apps.smbs_base.models import SiteModel, TimestampModel, ObjectMetadata, SettingsModel


class InventorySettings(SettingsModel):

    navigation_title = models.CharField(max_length=32, default=_('Products'))
    navigation_slug = models.CharField(max_length=32, default=_('products'))
    page_title = models.CharField(max_length=64, default=_('Product list'))

    @classmethod
    def get_settings(cls):
        cart_settings = cls.get_object()
        return cart_settings

    class Meta:
        verbose_name = _('Inventory Settings')


class Category(SiteModel, TimestampModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    slug = models.SlugField(max_length=255, unique=True)
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    class Meta:
        verbose_name = _('Categories')


class Item(SiteModel, TimestampModel):
    # Non-editable fields
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    slug = models.SlugField(max_length=255, unique=True)
    # Editable fields
    metadata = models.ForeignKey(ObjectMetadata, on_delete=models.SET_NULL,
                                 blank=True, null=True)
    language = models.CharField(max_length=10, choices=settings.LANGUAGES)
    publish_date = models.DateTimeField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True)
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    cover_image = models.ImageField(upload_to='smbs_inventory_images', blank=True, null=True)
    tags = TaggableManager()
    available_items = models.PositiveSmallIntegerField(default=1)
    in_stock = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)

    def get_absolute_url(self):
        return reverse('smbs_inventory:item-detail', args=[self.slug])

    def get_related_items(self):
        objects = self.tags.similar_objects()
        return [o for o in objects if isinstance(o, Item)]

    class Meta:
        ordering = ['-publish_date']
        verbose_name = _('Items')


class ItemReview(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    inventory_item = models.ForeignKey(Item, on_delete=models.CASCADE)
    positive_review = models.BooleanField(default=True)
    comment = models.TextField()
