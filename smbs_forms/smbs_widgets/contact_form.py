from django.template import Template, loader

from smbs_forms.forms import ContactForm


class Widget:

    NAME = 'Contact Form'

    def __init__(self, **kwargs):
        self.content = kwargs.get('content', '')
        self.context = kwargs.get('context')

    def render(self):
        form = ContactForm()
        if self.content:
            template = Template(self.content)
        else:
            template_file = 'smbs_widgets/contact_form.html'
            template = loader.get_template(template_file)
        return template.render({'form': form, 'csrf_token': self.context.get('csrf_token')})
