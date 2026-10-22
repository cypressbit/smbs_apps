from django.apps import AppConfig


class SmbsOauthConfig(AppConfig):
    name = 'smbs_apps.smbs_oauth'
    # Matches this app's migrations, whatever the host's DEFAULT_AUTO_FIELD.
    default_auto_field = 'django.db.models.AutoField'
    label = 'smbs_oauth'
    verbose_name = 'Social Login (OAuth)'
