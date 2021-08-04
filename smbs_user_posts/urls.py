from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required

from smbs_user_posts.views import (
    PostCreateView,
    PostListView,
    PostDetailView,
    PostCommentCreateView,
    PostReactionCreateView,
    PostCommentReactionCreateView
)


app_name = 'smbs_user_posts'


urlpatterns = [
    path('', PostListView.as_view(), name='post-list'),
    path(_('create/'), login_required(PostCreateView.as_view()), name='post-create'),
    path(_('comments/<int:pk>/<slug:slug>/'), PostDetailView.as_view(), name='post-detail'),
    path(_('comments/<int:pk>/<slug:slug>/add/'), PostCommentCreateView.as_view(), name='post-comment-add'),
    path(_('react/post/'), PostReactionCreateView.as_view(), name='post-reaction'),
    path(_('react/comment/'), PostCommentReactionCreateView.as_view(), name='post-comment-reaction'),
]
