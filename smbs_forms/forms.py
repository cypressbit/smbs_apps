from django.forms import ModelForm, PasswordInput

from smbs_forms.models import Contact, ContactFormSettings, ContactWithAddress, ContactWithAddressFormSettings


class FormSettings(ModelForm):

    class Meta:
        fields = [
            'email_enabled',
            'email_subject',
            'email_recipient',
            'email_user',
            'email_password',
            'email_host',
            'email_port',
            'success_url'
        ]
        widgets = {
            'email_password': PasswordInput(),
        }


class ContactFormSettingsForm(FormSettings):

    class Meta(FormSettings.Meta):
        model = ContactFormSettings


class ContactForm(ModelForm):

    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'message']


class ContactWithAddressFormSettingsForm(FormSettings):

    class Meta(FormSettings.Meta):
        model = ContactWithAddressFormSettings


class ContactWithAddressForm(ModelForm):

    class Meta:
        model = ContactWithAddress
        fields = ['name', 'email', 'phone', 'address', 'city', 'state', 'message']
