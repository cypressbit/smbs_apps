from django.apps import AppConfig


class SmbsUserPostsConfig(AppConfig):
    name = 'smbs_apps.smbs_user_posts'

    def ready(self):
        import smbs_apps.smbs_user_posts.signals
