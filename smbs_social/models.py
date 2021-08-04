from django.db import models

from smbs_base.models import SettingsModel


class SocialSettings(SettingsModel):
    enable_fb_pages_popup = models.BooleanField(default=False)
    fb_pages_script = models.TextField(blank=True)
    fb_pages_popup_delay = models.IntegerField(default=10000)
