from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class IconList(BaseWidget):
    key = 'icon_list'
    NAME = 'Icon list'
    category = 'basic'
    icon = 'list-check'
    description = 'Short lines of text, each with an icon.'
    ai_hint = 'Short facts (address, phone, perks). 2–8 items, a few words each.'
    template = 'smbs_widgets/v2/icon_list.html'

    class Props(fields.Schema):
        items = fields.Repeater(
            fields.Schema(
                icon=fields.Icon(default='check-circle'),
                text=fields.Text(max_length=160, default='A short point'),
                link=fields.Link(required=False),
            ),
            min_items=1, max_items=12,
            default=[{'icon': 'check-circle', 'text': 'A short point', 'link': None}],
        )
        columns = fields.Choice([1, 2, 3])
