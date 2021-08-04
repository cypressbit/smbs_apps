from django.urls import path
from django.utils.translation import gettext_lazy as _

from smbs_qa.views import QuestionCreateView, QuestionListView, QuestionDetailView, QuestionCommentCreateView


app_name = 'smbs_qa'


urlpatterns = [
    path('', QuestionListView.as_view(), name='question-list'),
    path(_('create/'), QuestionCreateView.as_view(), name='question-create'),
    path(_('comments/<int:pk>/<slug:slug>/'), QuestionDetailView.as_view(), name='question-detail'),
    path(_('comments/<int:pk>/<slug:slug>/add/'), QuestionCommentCreateView.as_view(), name='question-comment-add')
]
