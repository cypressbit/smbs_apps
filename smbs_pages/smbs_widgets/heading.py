from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class Heading(BaseWidget):
    key = 'heading'
    NAME = 'Heading'
    category = 'basic'
    icon = 'type-h1'
    description = 'A title, with an optional small label above it.'
    ai_hint = 'Short and specific. Use level 1 only once per page, for the main title.'
    template = 'smbs_widgets/v2/heading.html'

    class Props(fields.Schema):
        text = fields.Text(max_length=160, default='Your heading')
        level = fields.Choice([2, 1, 3, 4], label='Level')
        eyebrow = fields.Text(max_length=60, required=False, label='Label above')
        size = fields.Choice(['default', 'display', 'small'])
