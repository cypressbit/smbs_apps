from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class RichText(BaseWidget):
    key = 'rich_text'
    NAME = 'Text'
    category = 'basic'
    icon = 'text-paragraph'
    description = 'Paragraphs, lists and links.'
    ai_hint = 'One to three short paragraphs. Plain, specific language; no filler.'
    template = 'smbs_widgets/v2/rich_text.html'

    class Props(fields.Schema):
        html = fields.RichText(default='<p>Write something here.</p>')
        lead = fields.Bool(label='Larger intro text')
