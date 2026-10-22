from django.apps import AppConfig


class SmbsQaConfig(AppConfig):
    name = 'smbs_apps.smbs_qa'
    # Matches this app's migrations, whatever the host's DEFAULT_AUTO_FIELD.
    default_auto_field = 'django.db.models.AutoField'
