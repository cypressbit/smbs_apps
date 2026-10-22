from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class Testimonials(BaseWidget):
    key = 'testimonials'
    NAME = 'Testimonials'
    category = 'social-proof'
    icon = 'chat-quote'
    description = 'Quotes from customers.'
    ai_hint = ('Use real quotes from the brief. If there are none, write clearly generic placeholders with names '
               'like "Customer name" and set sample to true; never invent real-sounding people.')
    template = 'smbs_widgets/v2/testimonials.html'

    class Props(fields.Schema):
        layout = fields.Choice(['grid', 'carousel'])
        sample = fields.Bool(label='Sample content (shows a badge until you replace it)')
        items = fields.Repeater(
            fields.Schema(
                quote=fields.Text(max_length=500, multiline=True, default='A short quote from a happy customer.'),
                name=fields.Text(max_length=80, default='Customer name'),
                role=fields.Text(max_length=80, required=False),
                photo=fields.Image(required=False),
            ),
            min_items=1, max_items=12,
            default=[{'quote': 'A short quote from a happy customer.', 'name': 'Customer name', 'role': '', 'photo': None}],
        )
