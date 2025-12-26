import mimetypes
import os

from django.contrib import admin
from django.utils.html import format_html

from smbs_apps.smbs_pages.models import Page, Column, Row, Container, Widget, Media, Template


class MediaAdmin(admin.ModelAdmin):
    list_display = ("id", "media_type", "filename", "file_url_display", "name")
    list_filter = ("media_type",)
    search_fields = ("name", "file")

    def filename(self, obj: Media) -> str:
        return os.path.basename(obj.file.name) if obj.file else ""
    filename.short_description = "Filename"

    def file_url_display(self, obj: Media) -> str:
        if not obj.file:
            return ""
        url = obj.file_url
        # show URL and make it clickable
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    file_url_display.short_description = "File URL"


class PageAdmin(admin.ModelAdmin):
    list_display = ('created', 'name')


class WidgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'created')


admin.site.register(Page, PageAdmin)
admin.site.register(Widget, WidgetAdmin)
admin.site.register(Column)
admin.site.register(Row)
admin.site.register(Container)
admin.site.register(Media)
admin.site.register(Template)
