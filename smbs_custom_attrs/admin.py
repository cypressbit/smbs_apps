from django.contrib import admin
from smbs_apps.smbs_custom_attrs.models import CustomAttribute


@admin.register(CustomAttribute)
class CustomAttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'content_type', 'object_id', 'value')
    list_filter = ('content_type', 'name')
    search_fields = ('name', 'value')
