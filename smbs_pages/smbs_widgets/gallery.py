from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class Gallery(BaseWidget):
    key = 'gallery'
    NAME = 'Gallery'
    category = 'media'
    icon = 'images'
    description = 'A grid of images.'
    ai_hint = 'Images of real work or the place itself. Every image needs alt text.'
    template = 'smbs_widgets/v2/gallery.html'

    class Props(fields.Schema):
        layout = fields.Choice(['grid', 'masonry'])
        columns = fields.Choice([3, 2, 4])
        images = fields.Repeater(
            fields.Schema(image=fields.Image(required=False), caption=fields.Text(max_length=160, required=False)),
            min_items=2, max_items=24,
            default=[{'image': None, 'caption': ''}, {'image': None, 'caption': ''}, {'image': None, 'caption': ''}],
        )
