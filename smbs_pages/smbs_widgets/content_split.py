from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.smbs_widgets._common import buttons
from smbs_apps.smbs_pages.widgets import BaseWidget


class ContentSplit(BaseWidget):
    key = 'content_split'
    NAME = 'Image and text'
    category = 'content'
    icon = 'layout-split'
    description = 'An image beside a heading, text and optional buttons.'
    ai_hint = 'Tell one story (about us, a service, the process). Heading under 8 words, 1–2 short paragraphs.'
    template = 'smbs_widgets/v2/content_split.html'

    class Props(fields.Schema):
        image = fields.Image(required=False)
        image_side = fields.Choice(['left', 'right'])
        eyebrow = fields.Text(max_length=60, required=False, label='Label above')
        heading = fields.Text(max_length=120, default='Tell your story')
        body = fields.RichText(default='<p>A few sentences about who you are and how you work.</p>')
        buttons = buttons(with_default=False)
