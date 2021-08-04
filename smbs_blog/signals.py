from django.db.models.signals import pre_save

from smbs_blog.models import Post
from smbs_blog.metadata import create_post_metadata


def create_metadata_handler(sender, instance, **kwargs):
    if not kwargs.get('raw'):
        metadata = create_post_metadata(instance)
        instance.metadata = metadata


pre_save.connect(create_metadata_handler, sender=Post)
