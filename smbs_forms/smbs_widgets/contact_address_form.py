from django.template import Template, loader

from smbs_forms.forms import ContactWithAddressForm


class Widget:

    NAME = 'Contact Form With Address'

    def __init__(self, **kwargs):
        self.content = kwargs.get('content', '')
        self.context = kwargs.get('context')

    def render(self):
        form = ContactWithAddressForm()
        if self.content:
            template = Template(self.content)
        else:
            template_file = 'smbs_widgets/contact_address_form.html'
            template = loader.get_template(template_file)
        return template.render({'form': form, 'csrf_token': self.context.get('csrf_token')})
