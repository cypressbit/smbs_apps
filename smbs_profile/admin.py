from django.contrib import admin

from smbs_apps.smbs_profile.models import LocationProfile


class LocationProfileAdmin(admin.ModelAdmin):
    list_display = ('updated', 'user')


admin.site.register(LocationProfile, LocationProfileAdmin)
