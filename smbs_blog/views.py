import datetime

from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import get_language

from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView

from django.urls import reverse

from smbs_base.views import SMBSView, SMBSObjectMetadataView
from smbs_blog.models import Post, BlogSettings
from smbs_blog.forms import PostForm


class PostListView(SMBSView, ListView):
    model = Post
    name = 'blog'

    def get_context_data(self, **kwargs):
        context = super(PostListView, self).get_context_data(**kwargs)
        settings = BlogSettings.get_settings()
        context['blog_settings'] = settings
        return context


class PostDetailView(SMBSObjectMetadataView, DetailView):
    model = Post

    def get_context_data(self, **kwargs):
        context = super(PostDetailView, self).get_context_data(**kwargs)
        settings = BlogSettings.get_settings()
        if settings.get('comments_enabled'):
            context['comments'] = self.object.postcomment_set.all()
        context['blog_settings'] = settings
        return context


class PostCreateView(CreateView):
    model = Post
    form_class = PostForm

    def get_success_url(self):
        return reverse('smbs_blog:post-edit', kwargs={'pk': self.object.id})

    def get_initial(self):
        initial = super(PostCreateView, self).get_initial()
        initial['author'] = self.request.user.pk
        initial['language'] = get_language()
        initial['publish_date'] = datetime.datetime.now()
        initial['site'] = get_current_site(self.request)

        placeholder = 'Placeholder'
        initial['content'] = placeholder
        initial['title'] = placeholder
        initial['slug'] = placeholder
        return initial

    def get_context_data(self, **kwargs):
        context = super(PostCreateView, self).get_context_data(**kwargs)
        context['opts'] = self.model._meta
        return context


class PostUpdateView(UpdateView):
    model = Post
    form_class = PostForm

    def get_success_url(self):
        return reverse('smbs_blog:post-edit', kwargs={'pk': self.object.id})
