from django.apps import AppConfig


class SmbsSiteNotificationsConfig(AppConfig):
    name = 'smbs_apps.smbs_alerts'
    # Matches this app's migrations, whatever the host's DEFAULT_AUTO_FIELD.
    default_auto_field = 'django.db.models.AutoField'
