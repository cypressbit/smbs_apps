from taggit.managers import TaggableManager

from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

from smbs_apps.smbs_base.models import SiteModel, TimestampModel, SettingsModel, ObjectMetadata
from smbs_apps.smbs_comments_tree.models import Comment
from smbs_apps.smbs_blog.seo import run_seo_checks


class BlogSettings(SettingsModel):
    COMMENTS_ENABLED = False
    MIN_WORD_COUNT = 500
    MIN_TAG_COUNT = 4
    MIN_INTERNAL_LINK_COUNT = 1
    MIN_EXTERNAL_LINK_COUNT = 1
    MIN_IMAGE_COUNT = 1
    MIN_KEYWORD_COUNT = 2
    SEO_CHECKS = [
        'word_count',
        'tags',
        'images',
        'internal_links',
        'external_links',
        'keywords',
    ]
    SEO_CHECKS_CHOICES = (
        ('word_count', 'Word count'),
        ('tags', 'Tag count'),
        ('images', 'Image count'),
        ('internal_links', 'Internal link count'),
        ('external_links', 'External link count'),
        ('keywords', 'Keyword count'),
    )

    blog_metadata = models.TextField(blank=True)
    comments_enabled = models.BooleanField(default=COMMENTS_ENABLED)
    minimum_word_count = models.PositiveSmallIntegerField(default=MIN_WORD_COUNT)
    minimum_tag_count = models.PositiveSmallIntegerField(default=MIN_TAG_COUNT)
    minimum_internal_link_count = models.PositiveSmallIntegerField(default=MIN_INTERNAL_LINK_COUNT)
    minimum_external_link_count = models.PositiveSmallIntegerField(default=MIN_EXTERNAL_LINK_COUNT)
    minimum_image_count = models.PositiveSmallIntegerField(default=MIN_IMAGE_COUNT)
    minimum_keyword_count = models.PositiveSmallIntegerField(default=MIN_KEYWORD_COUNT)
    seo_checks = ArrayField(
        models.CharField(choices=SEO_CHECKS_CHOICES, max_length=24, blank=True),
        verbose_name='SEO checks', default=list
    )

    @classmethod
    def get_enabled_checks(cls):
        if cls.objects.exists():
            settings = cls.objects.first()

            return settings.seo_checks

        return cls.SEO_CHECKS

    @classmethod
    def get_settings(cls):
        settings = cls.get_object()

        response = {
            'comments_enabled': getattr(settings, 'comments_enabled', cls.COMMENTS_ENABLED),
            'word_count': {
                'min_count': getattr(settings, 'minimum_word_count', cls.MIN_WORD_COUNT),
            },
            'tags': {
                'min_count': getattr(settings, 'minimum_tag_count', cls.MIN_TAG_COUNT),
            },
            'images': {
                'min_count': getattr(settings, 'minimum_image_count', cls.MIN_IMAGE_COUNT),
            },
            'internal_links': {
                'min_count': getattr(settings, 'minimum_internal_link_count', cls.MIN_INTERNAL_LINK_COUNT),
            },
            'external_links': {
                'min_count': getattr(settings, 'minimum_external_link_count', cls.MIN_EXTERNAL_LINK_COUNT),
            },
            'keywords': {
                'min_count': getattr(settings, 'minimum_keyword_count', cls.MIN_KEYWORD_COUNT),
            },
        }

        return response

    class Meta:
        verbose_name = 'Blog Settings'


class Post(SiteModel, TimestampModel):
    # Non-editable fields
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=255, unique=True)
    checks = JSONField(default=dict, blank=True, editable=False)
    # Editable fields
    metadata = models.ForeignKey(ObjectMetadata, on_delete=models.DO_NOTHING,
                                 blank=True, null=True)
    publish_date = models.DateTimeField()
    language = models.CharField(max_length=10, choices=settings.LANGUAGES)
    title = models.CharField(max_length=255, unique=True)
    cover_image = models.ImageField(upload_to='smbs_blog_images', blank=True)
    content = models.TextField()
    description = models.CharField(max_length=300)
    tags = TaggableManager()
    is_draft = models.BooleanField(default=True)

    def get_absolute_url(self):
        return reverse('smbs_blog:post-detail', args=[self.slug])

    def clean(self):
        if not self.cover_image:
            raise ValidationError(_('Cover image is required'))

        enabled_checks = BlogSettings.get_enabled_checks()
        blog_settings = BlogSettings.get_settings()
        seo_checks, errors = run_seo_checks(enabled_checks, blog_settings, self)
        self.checks['seo'] = seo_checks
        if errors:
            if not self.is_draft:
                messages = [_('SEO validation failed')]
                messages.extend(errors)
                raise ValidationError(errors)

        self.checks['seo'] = seo_checks

    class Meta:
        ordering = ['-publish_date']


class PostComment(Comment):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
