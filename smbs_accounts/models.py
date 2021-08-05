from django.db import models

from smbs_apps.smbs_pages.models import Page
from smbs_apps.smbs_base.models import SettingsModel


class AccountSettings(SettingsModel):
    terms_of_service = models.ForeignKey(Page, blank=True, null=True, on_delete=models.CASCADE, related_name='tos')
    privacy_policy = models.ForeignKey(Page, blank=True, null=True, on_delete=models.CASCADE, related_name='privacy')
    signup_redirect = models.ForeignKey(Page, blank=True, null=True, on_delete=models.CASCADE, related_name='signup')
    login_redirect = models.ForeignKey(Page, blank=True, null=True, on_delete=models.CASCADE, related_name='login')

