from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse

from smbs_comments_tree.views import CommentCreateView
from smbs_reactions.views import ReactionCreateView
from smbs_user_posts.models import UserPost, UserPostComment, UserPostReaction, UserPostCommentReaction, UserPostSettings
from smbs_user_posts.forms import UserPostCommentForm
from smbs_base.views import SMBSObjectMetadataView


class PostListView(ListView):
    model = UserPost
    template_name = 'smbs_user_posts/userpost_list.html'

    def get_queryset(self):
        return UserPost.objects.all().annotate(reaction_count=Count('reactions')).order_by('-reaction_count', '-created')


class PostDetailView(SMBSObjectMetadataView, DetailView):
    model = UserPost
    template_name = 'smbs_user_posts/userpost_detail.html'

    def get_context_data(self, **kwargs):
        context = super(PostDetailView, self).get_context_data(**kwargs)
        context['comments'] = self.object.userpostcomment_set.all()
        context['comment_form'] = UserPostCommentForm(initial={
            'model_field_name': 'user_post',
            'model_instance_id': self.object.id
        })
        context['comment_form_action'] = reverse('smbs_user_posts:post-comment-add',
                                                 args=[str(self.object.id), self.object.slug])
        return context


class PostCreateView(CreateView):
    model = UserPost
    template_name = 'smbs_user_posts/userpost_form.html'
    fields = ('url', 'title', 'image', 'content', 'tags', 'is_anonymous')

    def get_success_url(self):
        return reverse('smbs_user_posts:post-detail', args=[str(self.object.id), self.object.slug])

    def form_valid(self, form):
        post_form = form.save(commit=False)
        post_form.user = self.request.user
        post_form.save()
        form.save_m2m()
        self.object = post_form
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(PostCreateView, self).get_context_data(**kwargs)
        context['default_tags'] = UserPostSettings.get_default_tags()
        return context


class PostCommentCreateView(CommentCreateView):
    model = UserPostComment
    form_class = UserPostCommentForm


class PostReactionCreateView(ReactionCreateView):
    model = UserPostReaction
    fields = ('reaction', 'user_post', 'user')


class PostCommentReactionCreateView(ReactionCreateView):
    update_count = True
    parent = 'user_post_comment'
    model = UserPostCommentReaction
    fields = ('reaction', 'user_post_comment', 'user')
