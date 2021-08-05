from django.contrib import admin

from smbs_apps.smbs_contact.models import ContactSettings


class ContactSettingsAdmin(admin.ModelAdmin):
    list_display = ('updated', 'site')


admin.site.register(ContactSettings, ContactSettingsAdmin)
