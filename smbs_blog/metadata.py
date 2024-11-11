from django.utils.text import Truncator

from smbs_apps.smbs_base.models import ObjectMetadata


def create_post_metadata(instance):
    title = Truncator(instance.title).chars(300)
    description = Truncator(instance.description).chars(300)
    metadata = ObjectMetadata.generate_base_metadata(
        title, description, instance.cover_image, instance.metadata
    )
    if instance.id:
        metadata.keywords = ','.join(instance.tags.names())
    metadata.og_type = 'article'
    metadata.twitter_card = 'summary_large_image'
    metadata.save()

    return metadata