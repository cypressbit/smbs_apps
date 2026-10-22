from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.smbs_widgets._common import buttons
from smbs_apps.smbs_pages.widgets import BaseWidget


class Hero(BaseWidget):
    key = 'hero'
    NAME = 'Hero'
    category = 'content'
    icon = 'window-fullscreen'
    description = 'The big opening block of a page: headline, short pitch, buttons and an image.'
    ai_hint = ('Headline states what the business does and for whom (under 10 words). Subheading adds one '
               'concrete benefit or location. One primary button.')
    template = 'smbs_widgets/v2/hero.html'

    class Props(fields.Schema):
        variant = fields.Choice(['centered', 'split', 'background_image'])
        eyebrow = fields.Text(max_length=60, required=False, label='Label above')
        heading = fields.Text(max_length=120, default='A clear promise to your customers')
        subheading = fields.Text(max_length=300, required=False, multiline=True,
                                 default='Say who you help and what makes you different, in one or two sentences.')
        buttons = buttons()
        image = fields.Image(required=False)
