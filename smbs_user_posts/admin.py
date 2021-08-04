from django.contrib import admin

from smbs_user_posts.models import UserPost, UserPostComment, UserPostReaction, UserPostSettings


class UserPostCommentAdmin(admin.ModelAdmin):
    list_display = ('created', 'user', 'text')


admin.site.register(UserPost)
admin.site.register(UserPostSettings)
admin.site.register(UserPostReaction)
admin.site.register(UserPostComment, UserPostCommentAdmin)

