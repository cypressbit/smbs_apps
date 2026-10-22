from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.smbs_widgets._common import buttons
from smbs_apps.smbs_pages.widgets import BaseWidget


class CtaBanner(BaseWidget):
    key = 'cta_banner'
    NAME = 'Call to action'
    category = 'content'
    icon = 'megaphone'
    description = 'A short, bold prompt to take the next step.'
    ai_hint = 'Heading is a direct invitation (under 8 words); text removes one objection.'
    template = 'smbs_widgets/v2/cta_banner.html'

    class Props(fields.Schema):
        heading = fields.Text(max_length=100, default='Ready to get started?')
        text = fields.Text(max_length=240, required=False, multiline=True, default='Tell us what you need and we will get back to you within a day.')
        buttons = buttons(min_items=1)
