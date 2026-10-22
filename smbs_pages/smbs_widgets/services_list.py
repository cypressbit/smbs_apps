from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class ServicesList(BaseWidget):
    key = 'services_list'
    NAME = 'Services'
    category = 'content'
    icon = 'card-list'
    description = 'Services or products with a description and optional price.'
    ai_hint = 'Use the offerings from the brief. Leave price empty unless the brief gives it.'
    template = 'smbs_widgets/v2/services_list.html'

    class Props(fields.Schema):
        layout = fields.Choice(['list', 'cards'])
        items = fields.Repeater(
            fields.Schema(
                icon=fields.Icon(required=False),
                title=fields.Text(max_length=80, default='A service'),
                description=fields.Text(max_length=400, multiline=True, required=False),
                price=fields.Text(max_length=32, required=False),
            ),
            min_items=1, max_items=24,
            default=[{'icon': 'check2', 'title': 'A service', 'description': 'What it includes.', 'price': ''}],
        )
