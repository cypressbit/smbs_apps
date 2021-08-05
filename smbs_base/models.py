from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.models import Site

from django.db import models

from smbs_apps.smbs_base.storage import OverwriteStorage


def site_logo_path(instance, filename):
    extension = filename.split('.')[-1]
    return 'site/images/logo.{}'.format(extension.lower())


def site_icon_path(instance, filename):
    extension = filename.split('.')[-1]
    return 'site/images/icon.{}'.format(extension.lower())


def site_css_path(instance, filename):
    return 'site/css/custom.css'


def theme_path(instance, filename):
    return 'site/css/theme.css'


def bootstrap_theme_path(instance, filename):
    return 'site/css/bootstrap.css'


def validate_image_extension(value):
    extension = value.name.split('.')[-1]
    if extension.lower() not in ['svg', 'png', 'jpg', 'jpeg']:
        raise ValidationError(_('Logo must be in SVG, PNG or JPG format'))


class SiteModel(models.Model):
    """
    Base site model.
    """
    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class TimestampModel(models.Model):
    """
    Base site model.
    """
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SettingsModel(SiteModel, TimestampModel):
    """
    Base settings model.
    """

    class Meta:
        abstract = True

    @classmethod
    def get_object(cls):
        site = Site.objects.get_current()
        try:
            obj = cls.objects.filter(site=site).first()
            return obj
        except cls.DoesNotExist:
            return None

    def clean(self):
        site = Site.objects.get_current()
        if self.__class__.objects.filter(site=site).exists() and not self.pk:
            raise ValidationError(_('There can only be one settings instance per site'))


class BaseSettings(SettingsModel):
    NAVBAR_LIGHT = 'navbar_light'
    NAVBAR_DARK = 'navbar_dark'

    NAVBAR_TYPES = [
        (NAVBAR_DARK, 'Dark'),
        (NAVBAR_LIGHT, 'Light'),
    ]

    # Brand
    logo = models.FileField(upload_to=site_logo_path,
                            validators=[validate_image_extension],
                            storage=OverwriteStorage(),
                            blank=True, null=True)
    icon = models.FileField(upload_to=site_icon_path,
                            validators=[validate_image_extension],
                            storage=OverwriteStorage(),
                            blank=True, null=True)
    # Tracking
    global_metadata = models.TextField(blank=True)
    # Email
    email_host = models.CharField(max_length=255, blank=True, null=True)
    email_port = models.PositiveSmallIntegerField(blank=True, null=True)
    email_user = models.CharField(max_length=255, blank=True, null=True)
    email_password = models.CharField(max_length=255, blank=True, null=True)
    email_use_tls = models.BooleanField(default=False)
    # Customization
    theme = models.FileField(upload_to=theme_path,
                             storage=OverwriteStorage(),
                             blank=True, null=True)
    navbar_type = models.CharField(max_length=64, choices=NAVBAR_TYPES, default=NAVBAR_LIGHT)
    custom_css = models.FileField(upload_to='site/css',
                                  blank=True, null=True)


class BaseMetadata(TimestampModel):
    title = models.CharField(max_length=60, blank=True, null=True)
    description = models.CharField(max_length=160, blank=True, null=True)
    keywords = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='smbs_base/metadata', blank=True, null=True)
    twitter_card = models.CharField(max_length=24, blank=True, null=True)
    twitter_site = models.CharField(max_length=24, blank=True, null=True)
    twitter_creator = models.CharField(max_length=24, blank=True, null=True)
    og_type = models.CharField(max_length=24, blank=True, null=True)
    og_fb_admins = models.CharField(max_length=24, blank=True, null=True)

    class Meta:
        abstract = True

    @classmethod
    def generate_base_metadata(cls, title, description, image, obj=None):
        if obj:
            metadata = obj
        else:
            metadata = cls()
        metadata.title = title
        metadata.description = description
        metadata.image = image.open()
        return metadata

    @staticmethod
    def get_site_name():
        site = Site.objects.get_current()
        return site.name

    def get_image_url(self):
        if self.image:
            site = Site.objects.get_current()
            return 'https://{}{}'.format(site.domain, self.image.url)


class ViewMetadata(BaseMetadata):
    view = models.CharField(max_length=255, unique=True)

    class Meta:
        get_latest_by = '-updated'


class ObjectMetadata(BaseMetadata):

    class Meta:
        get_latest_by = '-updated'
