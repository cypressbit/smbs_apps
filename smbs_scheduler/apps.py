from django.apps import AppConfig


class SmbsSchedulerConfig(AppConfig):
    name = 'smbs_apps.smbs_scheduler'
    verbose_name = 'Scheduler'
    # Matches this app's migrations, whatever the host's DEFAULT_AUTO_FIELD.
    default_auto_field = 'django.db.models.AutoField'
