from django.utils.translation import gettext_lazy as _
from django.contrib.sites.models import Site
from django.db import models

from smbs_apps.smbs_base.models import SiteModel, TimestampModel, SettingsModel
from smbs_apps.smbs_forms.validators import validate_phone


class FormSettings(SettingsModel):
    EMAIL_ENABLED = False

    email_subject = models.CharField(max_length=64, blank=True, null=True)
    email_recipient = models.EmailField(blank=True, null=True)
    email_enabled = models.BooleanField(default=EMAIL_ENABLED)
    email_user = models.CharField(max_length=64, blank=True, null=True)
    email_password = models.CharField(max_length=64, blank=True, null=True)
    email_host = models.CharField(max_length=64, blank=True, null=True)
    email_port = models.PositiveSmallIntegerField(blank=True, null=True)
    success_url = models.URLField(blank=True, null=True)

    class Meta:
        abstract = True

    @classmethod
    def get_settings(cls):
        form_settings = cls.get_object()
        response = {
            'email_enabled': getattr(form_settings, 'email_enabled', cls.EMAIL_ENABLED),
            'email_user': getattr(form_settings, 'email_user'),
            'email_password': getattr(form_settings, 'email_password'),
            'email_host': getattr(form_settings, 'email_host'),
            'email_port': getattr(form_settings, 'email_port'),
            'email_recipient': getattr(form_settings, 'email_recipient'),
            'email_subject': getattr(form_settings, 'email_subject', 'Contact Form'),
            'success_url': getattr(form_settings, 'success_url', '/') or '/',
        }
        return response

    def clean(self):
        self.site = Site.objects.get_current()


class ContactFormSettings(FormSettings):

    class Meta:
        verbose_name = _('Contact Form Settings')


class Contact(TimestampModel, SiteModel):

    name = models.CharField(max_length=64, help_text=_('Name'))
    email = models.EmailField(help_text=_('E-mail Address'))
    phone = models.CharField(max_length=24, validators=[validate_phone], help_text=_('Phone Number'))
    message = models.TextField(help_text=_('Message'))

    class Meta:
        verbose_name = _('Contact Form')

    def clean(self):
        self.site = Site.objects.get_current()


class ContactWithAddressFormSettings(FormSettings):

    class Meta:
        verbose_name = _('Contact Form With Address Settings')


class ContactWithAddress(TimestampModel, SiteModel):
    name = models.CharField(max_length=64, help_text=_('Name'))
    email = models.EmailField(help_text=_('E-mail Address'))
    phone = models.CharField(max_length=24, validators=[validate_phone], help_text=_('Phone Number'))
    address = models.CharField(max_length=128, help_text=_('Address'))
    city = models.CharField(max_length=64, help_text=_('City'))
    state = models.CharField(max_length=32, help_text=_('State'))
    message = models.TextField(help_text=_('Message'))

    class Meta:
        verbose_name = _('Contact Form With Address')

    def clean(self):
        self.site = Site.objects.get_current()
