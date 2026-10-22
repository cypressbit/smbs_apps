from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.smbs_widgets._common import button_item
from smbs_apps.smbs_pages.widgets import BaseWidget


def _plan(name, price, highlighted=False):
    return {'name': name, 'price': price, 'period': 'per month', 'description': '',
            'features': [{'text': 'A feature'}, {'text': 'Another feature'}], 'highlighted': highlighted,
            'button': {'label': 'Choose plan', 'link': {'kind': 'anchor', 'anchor': 'contact'}, 'style': 'primary', 'icon': ''}}


class PricingTable(BaseWidget):
    key = 'pricing_table'
    NAME = 'Pricing'
    category = 'content'
    icon = 'tags'
    description = 'Plans or packages side by side.'
    ai_hint = 'Only use prices given in the brief; otherwise use "Contact us" as the price text.'
    template = 'smbs_widgets/v2/pricing_table.html'

    class Props(fields.Schema):
        plans = fields.Repeater(
            fields.Schema(
                name=fields.Text(max_length=40, default='Plan'),
                price=fields.Text(max_length=24, default='Contact us'),
                period=fields.Text(max_length=24, required=False),
                description=fields.Text(max_length=160, required=False),
                features=fields.Repeater(fields.Schema(text=fields.Text(max_length=100, default='A feature')),
                                         max_items=12, required=False),
                highlighted=fields.Bool(),
                button=button_item('Choose plan'),
            ),
            min_items=1, max_items=4,
            default=[_plan('Basic', 'Contact us'), _plan('Standard', 'Contact us', True), _plan('Premium', 'Contact us')],
        )
