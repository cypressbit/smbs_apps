from django.apps import AppConfig


class SmbsBlogConfig(AppConfig):
    name = 'smbs_apps.smbs_blog'

    def ready(self):
        import smbs_apps.smbs_blog.signals

