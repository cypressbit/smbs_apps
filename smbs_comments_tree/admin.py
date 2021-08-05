from django.contrib import admin

from smbs_apps.smbs_comments_tree.models import Comment


class CommentAdmin(admin.ModelAdmin):
    list_display = ('created', 'user', 'text')
