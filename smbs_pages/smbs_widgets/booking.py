from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget, data


class Booking(BaseWidget):
    """
    Defined here so every host can validate it; the services, staff and free times come from the host
    ("booking.services"), which also provides the template and the URLs it books through.
    """
    key = 'booking'
    NAME = 'Booking'
    category = 'booking'
    icon = 'calendar-check'
    description = ('Visitors choose a service, a person and a time, and book it (with payment when the service '
                   'takes one).')
    ai_hint = 'Only on websites that take bookings. Never invent services, prices or hours: they’re the owner’s own.'
    capability = 'booking'
    template = 'smbs_widgets/v2/booking.html'

    class Props(fields.Schema):
        layout = fields.Choice(['booker', 'list'], label='Show',
                               help_text='The booking calendar, or the services with prices and “Book” buttons.')
        service = fields.Text(max_length=100, required=False, label='Service',
                              help_text='Optional: one service’s name, as in Booking › Services. Empty shows all.')
        show_prices = fields.Bool(default=True, label='Show prices')

    def get_context_data(self):
        context = super().get_context_data()
        context['services'] = data('booking.services', name=(self.props.get('service') or '').strip(),
                                   editing=bool(self.context.get('editing'))) or []
        return context
