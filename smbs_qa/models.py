from taggit.managers import TaggableManager

from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.contrib.sites.models import Site
from django.urls import reverse

from django.contrib.auth.models import User
from django.db import models

from smbs_comments_tree.models import Comment
from smbs_base.models import SiteModel, TimestampModel


class Question(SiteModel, TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('User'))
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    is_anonymous = models.BooleanField(default=False, verbose_name=_('Ask anonymously'))
    question = models.TextField(verbose_name=_('Question'))
    tags = TaggableManager(help_text=_(
        'A list of comma-separated tags related to your question, for example "health, fitness".'))
    slug = models.SlugField(max_length=255, editable=False)

    def clean(self):
        self.slug = slugify(self.title)
        self.site = Site.objects.get_current()


class QuestionComment(Comment):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('smbs_qa:question-detail',
                       args=[str(self.question.id), self.question.slug])
