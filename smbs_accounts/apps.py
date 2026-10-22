from django.apps import AppConfig


class SmbsAccountsConfig(AppConfig):
    name = 'smbs_apps.smbs_accounts'
    # Matches this app's migrations, whatever the host's DEFAULT_AUTO_FIELD.
    default_auto_field = 'django.db.models.AutoField'
