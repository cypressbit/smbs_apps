from django.contrib import admin

from smbs_apps.smbs_pages.models import Page, Column, Row, Container, Widget, Media


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
