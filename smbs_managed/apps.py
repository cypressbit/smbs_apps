from django.apps import AppConfig


class SmbsManagedConfig(AppConfig):
    name = 'smbs_apps.smbs_managed'
    label = 'smbs_managed'
    # Matches this app's migrations, whatever the host's DEFAULT_AUTO_FIELD.
    default_auto_field = 'django.db.models.AutoField'
    verbose_name = 'Managed site'
