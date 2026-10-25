from smbs_apps.smbs_forms import turnstile
from smbs_apps.smbs_forms.forms import ContactForm
from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class ContactFormBlock(BaseWidget):
    key = 'contact_form'
    NAME = 'Contact form'
    category = 'forms'
    icon = 'envelope'
    description = 'A contact form: name, email, phone and message. Submissions go to the site inbox.'
    ai_hint = 'Heading is an invitation (e.g. "Get a free quote"); intro says how fast you reply, if the brief says.'
    capability = 'forms'
    template = 'smbs_widgets/v2/contact_form.html'

    class Props(fields.Schema):
        heading = fields.Text(max_length=100, required=False, default='Get in touch')
        intro = fields.Text(max_length=300, required=False, multiline=True)
        button_label = fields.Text(max_length=40, default='Send message')

    def get_context_data(self):
        context = super().get_context_data()
        context['form'] = ContactForm()
        context['turnstile_site_key'] = turnstile.site_key() if turnstile.enabled() else ''
        return context
