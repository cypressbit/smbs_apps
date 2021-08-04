from django.db.models.signals import pre_save

from smbs_user_posts.models import UserPost
from smbs_user_posts.metadata import create_post_metadata


def create_metadata_handler(sender, instance, **kwargs):
    if not kwargs.get('raw'):
        metadata = create_post_metadata(instance)
        instance.metadata = metadata


pre_save.connect(create_metadata_handler, sender=UserPost)
