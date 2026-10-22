from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


DEFAULT_ITEMS = [
    {'icon': 'star', 'title': 'Quality first', 'body': 'A sentence about why this matters to customers.'},
    {'icon': 'clock', 'title': 'On time', 'body': 'A sentence about why this matters to customers.'},
    {'icon': 'emoji-smile', 'title': 'Friendly service', 'body': 'A sentence about why this matters to customers.'},
]


class FeatureGrid(BaseWidget):
    key = 'feature_grid'
    NAME = 'Feature grid'
    category = 'content'
    icon = 'grid-3x3-gap'
    description = 'Benefits or features in a grid, each with an icon, a title and a sentence.'
    ai_hint = '3–6 benefit statements: an icon, a 2–5 word title and one specific sentence each.'
    template = 'smbs_widgets/v2/feature_grid.html'

    class Props(fields.Schema):
        heading = fields.Text(max_length=100, required=False)
        columns = fields.Choice([3, 2, 4])
        cards = fields.Bool(label='Show as cards')
        items = fields.Repeater(
            fields.Schema(
                icon=fields.Icon(default='star'),
                title=fields.Text(max_length=60, default='A benefit'),
                body=fields.Text(max_length=240, multiline=True, required=False),
            ),
            min_items=2, max_items=8, default=DEFAULT_ITEMS,
        )
