from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class ButtonGroup(BaseWidget):
    key = 'button_group'
    NAME = 'Buttons'
    category = 'basic'
    icon = 'hand-index'
    description = 'One or more call-to-action buttons.'
    ai_hint = 'One primary action, at most one secondary. Labels are 1–4 words and start with a verb.'
    template = 'smbs_widgets/v2/button_group.html'

    class Props(fields.Schema):
        buttons = fields.Repeater(
            fields.Schema(
                label=fields.Text(max_length=40, default='Get in touch'),
                link=fields.Link(default={'kind': 'anchor', 'anchor': 'contact'}),
                style=fields.Choice(['primary', 'secondary', 'accent', 'link']),
                icon=fields.Icon(required=False),
            ),
            min_items=1, max_items=3,
            default=[{'label': 'Get in touch', 'link': {'kind': 'anchor', 'anchor': 'contact'}, 'style': 'primary', 'icon': ''}],
        )
        size = fields.Choice(['default', 'large', 'small'])
