from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


DEFAULT_ROWS = [
    {'day': 'Monday – Friday', 'hours': '9:00 – 17:00'},
    {'day': 'Saturday', 'hours': '10:00 – 14:00'},
    {'day': 'Sunday', 'hours': 'Closed'},
]


class Hours(BaseWidget):
    key = 'hours'
    NAME = 'Opening hours'
    category = 'content'
    icon = 'clock'
    description = 'Opening hours by day.'
    ai_hint = 'Only use hours from the brief; otherwise leave the default rows for the owner to edit.'
    template = 'smbs_widgets/v2/hours.html'

    class Props(fields.Schema):
        heading = fields.Text(max_length=60, required=False, default='Opening hours')
        rows = fields.Repeater(
            fields.Schema(day=fields.Text(max_length=40, default='Day'),
                          hours=fields.Text(max_length=60, default='9:00 – 17:00')),
            min_items=1, max_items=14, default=DEFAULT_ROWS,
        )
        note = fields.Text(max_length=200, required=False)
