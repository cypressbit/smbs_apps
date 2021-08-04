from django.contrib import admin

from smbs_base.admin import SettingsAdmin

from smbs_forms.models import ContactFormSettings, Contact
from smbs_forms.forms import ContactFormSettingsForm


class ContactFormSettingsAdmin(SettingsAdmin):
    form = ContactFormSettingsForm


class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'phone', 'message')


admin.site.register(Contact, ContactAdmin)
admin.site.register(ContactFormSettings, ContactFormSettingsAdmin)
