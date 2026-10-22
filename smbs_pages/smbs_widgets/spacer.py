from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class Spacer(BaseWidget):
    key = 'spacer'
    NAME = 'Spacer'
    category = 'basic'
    icon = 'arrows-vertical'
    description = 'Empty vertical space.'
    ai_hint = 'Rarely needed; sections already have padding.'
    template = 'smbs_widgets/v2/spacer.html'

    class Props(fields.Schema):
        size = fields.Choice(['md', 'sm', 'lg', 'xl'])
