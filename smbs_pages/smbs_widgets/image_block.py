from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.models import Media
from smbs_apps.smbs_pages.widgets import BaseWidget


class Image(BaseWidget):
    key = 'image'
    NAME = 'Image'
    category = 'media'
    icon = 'image'
    description = 'A single image with an optional caption and link.'
    template = 'smbs_widgets/v2/image.html'

    class Props(fields.Schema):
        image = fields.Image(required=False)
        caption = fields.Text(max_length=200, required=False)
        rounded = fields.Bool(default=True)
        aspect = fields.Choice(['natural', '16x9', '4x3', '1x1', '3x4'], label='Shape')
        link = fields.Link(required=False)

    def get_context_data(self):
        context = super().get_context_data()
        image = self.props.get('image')
        context['media'] = Media.objects.filter(pk=image['media']).first() if image else None
        return context
