from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView

from django.shortcuts import redirect
from django.urls import reverse

from smbs_comments_tree.views import CommentCreateView
from smbs_qa.models import Question, QuestionComment
from smbs_qa.forms import QuestionCommentForm


class QuestionListView(ListView):
    model = Question
    template_name = 'smbs_qa/question_list.html'


class QuestionDetailView(DetailView):
    model = Question
    template_name = 'smbs_qa/question_detail.html'

    def get_context_data(self, **kwargs):
        context = super(QuestionDetailView, self).get_context_data(**kwargs)
        context['comments'] = self.object.questioncomment_set.all()
        context['comment_form'] = QuestionCommentForm(initial={
            'model_field_name': 'question',
            'model_instance_id': self.object.id
        })
        context['comment_form_action'] = reverse('smbs_qa:question-comment-add',
                                                 args=[str(self.object.id), self.object.slug])
        return context


class QuestionCreateView(CreateView):
    model = Question
    template_name = 'smbs_qa/question_form.html'
    fields = ('title', 'question', 'tags', 'is_anonymous')

    def get_success_url(self):
        return '/foro'

    def form_valid(self, form):
        question_form = form.save(commit=False)
        question_form.user = self.request.user
        question_form.save()

        return redirect(self.get_success_url())


class QuestionCommentCreateView(CommentCreateView):
    model = QuestionComment
    form_class = QuestionCommentForm
