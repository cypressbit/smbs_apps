from urllib.parse import quote_plus

from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class LocationMap(BaseWidget):
    key = 'location_map'
    NAME = 'Map'
    category = 'content'
    icon = 'geo-alt'
    description = 'An embedded map of an address.'
    ai_hint = 'Use the exact address from the brief.'
    template = 'smbs_widgets/v2/location_map.html'

    class Props(fields.Schema):
        address = fields.Text(max_length=200, default='Times Square, New York, NY')
        height = fields.Choice(['md', 'sm', 'lg'])

    def get_context_data(self):
        context = super().get_context_data()
        context['embed_url'] = f'https://www.google.com/maps?q={quote_plus(self.props["address"])}&output=embed'
        context['height_px'] = {'sm': 240, 'md': 360, 'lg': 480}[self.props.get('height') or 'md']
        return context
