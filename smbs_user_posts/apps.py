from django.apps import AppConfig


class SmbsUserPostsConfig(AppConfig):
    name = 'smbs_user_posts'

    def ready(self):
        import smbs_user_posts.signals
