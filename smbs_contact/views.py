from django.views.generic.detail import DetailView

from smbs_contact.models import ContactSettings


class ContactView(DetailView):

    model = ContactSettings
    template_name = 'smbs_contact/contact.html'

    def get_object(self, queryset=None):
        return self.model.get_object()
