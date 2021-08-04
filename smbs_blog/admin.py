from django.contrib import admin

from smbs_base.admin import SettingsAdmin
from smbs_blog.models import Post, BlogSettings


class BlogSettingsAdmin(SettingsAdmin):
    pass


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'publish_date')


admin.site.register(Post, PostAdmin)
admin.site.register(BlogSettings, BlogSettingsAdmin)
