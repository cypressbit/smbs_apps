from django.contrib import admin

from smbs_qa.models import Question, QuestionComment


class QuestionCommentAdmin(admin.ModelAdmin):
    list_display = ('created', 'user', 'text')


admin.site.register(QuestionComment, QuestionCommentAdmin)

