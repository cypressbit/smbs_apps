from django.contrib.auth.models import User

from django.db import models

from smbs_base.models import SiteModel, TimestampModel, SettingsModel


class NewsletterSettings(SettingsModel):
    MAILCHIMP = 'mailchimp'
    BACKEND_CHOICES = (
        (MAILCHIMP, 'Mailchimp'),
    )

    backend = models.CharField(max_length=24, choices=BACKEND_CHOICES, default=MAILCHIMP)


class NewsletterOptIn(SiteModel, TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    terms = models.TextField()


