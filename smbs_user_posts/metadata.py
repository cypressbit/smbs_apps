import extraction
import requests

from django.utils.text import Truncator

from smbs_base.models import ObjectMetadata
from smbs_user_posts.utils import get_extraction


def create_post_metadata(instance):
    if instance.url:
        extracted = get_extraction(instance.url)
        title = Truncator(instance.title or extracted.title).chars(60)
        description = Truncator(extracted.description).chars(160)
        image = instance.image or extracted.image
        metadata = ObjectMetadata.generate_base_metadata(
            title, description, image, instance.metadata
        )
    else:
        title = Truncator(instance.title).chars(60)
        description = Truncator(instance.content).chars(160)
        metadata = ObjectMetadata.generate_base_metadata(
            title, description, instance.image, instance.metadata
        )
    if instance.id:
        metadata.keywords = ','.join(instance.tags.names())
    metadata.og_type = 'article'
    metadata.twitter_card = 'summary_large_image'
    metadata.save()

    return metadata
