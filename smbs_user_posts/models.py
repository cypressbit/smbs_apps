import os
import io

import requests

from taggit.managers import TaggableManager

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.contrib.sites.models import Site
from django.contrib.postgres.fields import ArrayField
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.db import models

from smbs_reactions.models import Reaction
from smbs_reactions.mixins import ReactionMixin
from smbs_comments_tree.models import Comment
from smbs_base.models import SiteModel, TimestampModel, SettingsModel, ObjectMetadata
from smbs_user_posts.utils import get_extraction


class UserPostSettings(SettingsModel):
    COMMENTS_ENABLED = True

    comments_enabled = models.BooleanField(default=COMMENTS_ENABLED)
    default_image = models.ImageField(upload_to='user_posts', verbose_name=_('Image'), blank=True, null=True)
    default_tags = ArrayField(
        models.CharField(max_length=32, blank=True), verbose_name='Default post tags', default=list
    )

    @classmethod
    def get_default_tags(cls):
        settings = cls.get_object()
        if settings:
            return settings.default_tags
        return []

    class Meta:
        verbose_name = 'User Post Settings'


class UserPost(SiteModel, TimestampModel, ReactionMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('User'))
    metadata = models.ForeignKey(ObjectMetadata, on_delete=models.DO_NOTHING,
                                 blank=True, null=True)
    title = models.CharField(max_length=255, verbose_name=_('Title'), blank=True, null=True)
    is_anonymous = models.BooleanField(default=False, verbose_name=_('Post anonymously'))
    image = models.ImageField(upload_to='user_posts', verbose_name=_('Image'), blank=True, null=True)
    url = models.URLField(verbose_name=_('URL'), blank=True, null=True)
    content = models.TextField(verbose_name=_('Content'), blank=True, null=True)
    tags = TaggableManager(help_text=_(
        'A list of comma-separated tags related to your post.'))
    slug = models.SlugField(max_length=255, editable=False)

    def get_absolute_url(self):
        return reverse('smbs_user_posts:post-detail', args=[self.id, self.slug])

    def clean(self):
        self.site = Site.objects.get_current()
        if self.url:
            try:
                extracted = get_extraction(self.url)
            except requests.exceptions.HTTPError:
                raise ValidationError(_('Could not get URL content.'))
            if not self.title:
                self.title = extracted.title
            if not self.content:
                self.content = extracted.description
            if not self.image:
                try:
                    result = requests.get(extracted.image)
                    result.raise_for_status()
                    self.image = SimpleUploadedFile(
                        os.path.basename(extracted.image),
                        io.BytesIO(result.content).read()
                    )
                except requests.exceptions.HTTPError:
                    pass
        if not self.title:
            raise ValidationError(_('Your post needs a title.'))
        if not self.content and not self.image:
            raise ValidationError(_('Your post needs content.'))
        if not self.image:
            post_settings = UserPostSettings.get_object()
            if post_settings:
                self.image = post_settings.default_image
        self.slug = slugify(self.title)


class UserPostComment(Comment):
    user_post = models.ForeignKey(UserPost, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('smbs_user_posts:post-detail',
                       args=[str(self.user_post.id), self.user_post.slug])


class UserPostReaction(Reaction):
    user_post = models.ForeignKey(UserPost, on_delete=models.CASCADE, related_name='reactions')


class UserPostCommentReaction(Reaction):
    user_post_comment = models.ForeignKey(UserPostComment, on_delete=models.CASCADE, related_name='reactions')
