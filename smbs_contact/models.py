from django.db import models

from smbs_apps.smbs_base.models import SettingsModel


class ContactSettings(SettingsModel):
    display_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=24, blank=True, null=True)
    email_address = models.EmailField(blank=True, null=True)
    google_maps_location_script = models.TextField(blank=True)
