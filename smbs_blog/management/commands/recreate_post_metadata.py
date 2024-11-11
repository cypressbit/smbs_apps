from django.core.management.base import BaseCommand

from smbs_apps.smbs_blog.models import Post
from smbs_apps.smbs_blog.metadata import create_post_metadata


class Command(BaseCommand):
    help = 'Recreate the metadata for all posts'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--post-id',
            dest='post_id',
            help='Post id to recreate metadata for',
            type=int,
        )

    def handle(self, *args, **options):
        if options.get('post_id'):
            posts = Post.objects.filter(id=options.get('post_id'))
        else:
            posts = Post.objects.all()

        for post in posts:
            print('Recreating metadata for post object {}'.format(post.id))
            post.metadata = create_post_metadata(post)
            post.save_base(raw=True)
