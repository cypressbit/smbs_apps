from django.apps import AppConfig


class SmbsBlogConfig(AppConfig):
    name = 'smbs_blog'

    def ready(self):
        import smbs_blog.signals

