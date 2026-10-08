from django.conf import settings
from django.db import models

from smbs_apps.smbs_base.models import SettingsModel


class GoogleAccount(models.Model):
    """Links a Django User to the Google account they signed in with.
    `google_sub` is Google's stable, unique subject identifier for the
    account (never the email, which a user could change on Google's side)."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='google_account',
    )
    google_sub = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} <-> {self.email}"


class GoogleOAuthSettings(SettingsModel):
    """Admin-editable Google OAuth client credentials — same one-row-per-Site
    singleton pattern as organizations.models.StripePlanSettings. Falls back
    to the GOOGLE_OAUTH_CLIENT_ID/_SECRET Django settings only if blank, so a
    new client can be rotated in from Google Cloud Console without a redeploy."""
    client_id = models.CharField(
        max_length=255, blank=True,
        help_text="OAuth 2.0 Client ID from Google Cloud Console (APIs & Services -> Credentials).",
    )
    client_secret = models.CharField(
        max_length=255, blank=True,
        help_text="OAuth 2.0 Client Secret from Google Cloud Console.",
    )

    def __str__(self):
        return f"Google OAuth settings ({self.site})"


def get_google_oauth_credentials():
    """Returns (client_id, client_secret): admin row first, Django setting
    fallback — same chain as organizations.models.get_capture_price_id()."""
    plan_settings = GoogleOAuthSettings.get_object()
    client_id = (plan_settings and plan_settings.client_id) or getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '') or ''
    client_secret = (plan_settings and plan_settings.client_secret) or getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', '') or ''
    return client_id, client_secret
