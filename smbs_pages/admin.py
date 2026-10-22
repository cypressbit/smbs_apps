import mimetypes
import os

from django.contrib import admin
from django.utils.html import format_html

from smbs_apps.smbs_pages import services
from smbs_apps.smbs_pages.models import (
    Page, Column, Row, Container, Widget, Media, Template, PageRevision, SiteChrome,
)


class MediaAdmin(admin.ModelAdmin):
    list_display = ("id", "media_type", "source", "filename", "file_url_display", "name", "alt_text")
    list_filter = ("media_type", "source")
    search_fields = ("name", "file", "alt_text", "remote_url")

    def filename(self, obj: Media) -> str:
        return os.path.basename(obj.file.name) if obj.file else ""
    filename.short_description = "Filename"

    def file_url_display(self, obj: Media) -> str:
        url = obj.url
        if not url:
            return ""
        # show URL and make it clickable
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    file_url_display.short_description = "File URL"


class PageRevisionInline(admin.TabularInline):
    model = PageRevision
    fields = ('number', 'note', 'created_by', 'created')
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.action(description='Publish the current draft')
def publish_drafts(modeladmin, request, queryset):
    for page in queryset:
        if page.draft.get('sections'):
            services.publish_page(page, user=request.user, note='Published from admin')


class PageAdmin(admin.ModelAdmin):
    list_display = ('created', 'name', 'slug', 'content_mode', 'published_revision', 'active')
    list_filter = ('content_mode', 'active')
    readonly_fields = ('draft_version', 'published_revision')
    inlines = [PageRevisionInline]
    actions = [publish_drafts]


class WidgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'created')


admin.site.register(Page, PageAdmin)
admin.site.register(Widget, WidgetAdmin)
admin.site.register(Column)
admin.site.register(Row)
admin.site.register(Container)
admin.site.register(Media, MediaAdmin)
admin.site.register(Template)
admin.site.register(SiteChrome)
