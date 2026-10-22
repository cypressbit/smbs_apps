from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class Stats(BaseWidget):
    key = 'stats'
    NAME = 'Numbers'
    category = 'content'
    icon = 'bar-chart'
    description = 'A few key numbers with labels.'
    ai_hint = 'Only use numbers given in the brief. Never invent statistics.'
    template = 'smbs_widgets/v2/stats.html'

    class Props(fields.Schema):
        items = fields.Repeater(
            fields.Schema(
                value=fields.Text(max_length=16, default='10+'),
                label=fields.Text(max_length=60, default='Years in business'),
            ),
            min_items=2, max_items=4,
            default=[{'value': '10+', 'label': 'Years in business'}, {'value': '500+', 'label': 'Happy customers'}],
        )
