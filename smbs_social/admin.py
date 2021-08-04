from django.contrib import admin

from smbs_social.models import SocialSettings


class SocialSettingsAdmin(admin.ModelAdmin):
    list_display = ('created',)


admin.site.register(SocialSettings, SocialSettingsAdmin)
