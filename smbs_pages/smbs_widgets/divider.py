from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class Divider(BaseWidget):
    key = 'divider'
    NAME = 'Divider'
    category = 'basic'
    icon = 'dash-lg'
    description = 'A horizontal line.'
    ai_hint = 'Use sparingly, to separate related content inside a section.'
    template = 'smbs_widgets/v2/divider.html'

    class Props(fields.Schema):
        style = fields.Choice(['line', 'short', 'dotted'])
