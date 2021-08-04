from django.urls import path, re_path
from django.contrib.admin.views.decorators import staff_member_required

from smbs_blog.views import PostCreateView, PostListView, PostDetailView, PostUpdateView


app_name = 'smbs_blog'


urlpatterns = [
    path('post/', staff_member_required(PostCreateView.as_view()), name='post-create'),
    re_path('post/edit/(?P<pk>\d+)/', staff_member_required(PostUpdateView.as_view()), name='post-edit'),
    path('', PostListView.as_view(), name='post-list'),
    re_path(r'^(?P<slug>[\w-]+)/$', PostDetailView.as_view(), name='post-detail'),
]
