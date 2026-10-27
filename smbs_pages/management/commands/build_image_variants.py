from django.core.management.base import BaseCommand

from smbs_apps.smbs_pages import images
from smbs_apps.smbs_pages.models import Media


class Command(BaseCommand):
    help = 'Makes the smaller copies of uploaded images that are missing them. Safe to run repeatedly.'

    def handle(self, *args, **options):
        built = 0
        for media in Media.objects.filter(media_type=Media.IMAGE).exclude(file='').iterator():
            if media.variants.get('source') != media.file.name:
                images.update_variants(media)
                built += 1
        self.stdout.write(f'Made smaller copies of {built} image(s).')
