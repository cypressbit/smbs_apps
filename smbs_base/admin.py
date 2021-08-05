from django.contrib import admin

from smbs_apps.smbs_base.models import BaseSettings, ObjectMetadata, ViewMetadata


class SettingsAdmin(admin.ModelAdmin):
    list_display = ('updated', 'site')


class BaseSettingsAdmin(SettingsAdmin):
    pass


admin.site.register(BaseSettings, BaseSettingsAdmin)
admin.site.register(ObjectMetadata)
admin.site.register(ViewMetadata)
