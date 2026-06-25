from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
import datetime

from smbs_apps.smbs_blog.models import Post, PostComment


class PostCommentSanitizationTest(TestCase):
    """
    Tests bleach HTML sanitization in Comment.save() via the concrete PostComment subclass.
    """

    def setUp(self):
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(username='commenter', password='pass')
        self.post = Post.objects.create(
            site=self.site,
            author=self.user,
            slug='test-post',
            title='Test Post',
            content='<p>Content</p>',
            description='A test post description',
            publish_date=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
            language='en',
            is_draft=True,
        )

    def test_script_tags_stripped(self):
        comment = PostComment(
            post=self.post,
            user=self.user,
            text='<script>alert("xss")</script>Hello',
        )
        comment.save()
        self.assertNotIn('<script>', comment.text)
        self.assertIn('Hello', comment.text)

    def test_plain_text_preserved(self):
        comment = PostComment(
            post=self.post,
            user=self.user,
            text='This is a plain comment.',
        )
        comment.save()
        self.assertIn('This is a plain comment.', comment.text)

    def test_str_is_text(self):
        comment = PostComment(
            post=self.post,
            user=self.user,
            text='My comment text',
        )
        comment.save()
        self.assertEqual(str(comment), comment.text)

    def test_deleted_defaults_false(self):
        comment = PostComment.objects.create(
            post=self.post,
            user=self.user,
            text='Not deleted',
        )
        self.assertFalse(comment.deleted)

    def test_reaction_count_defaults_zero(self):
        comment = PostComment.objects.create(
            post=self.post,
            user=self.user,
            text='No reactions yet',
        )
        self.assertEqual(comment.reaction_count, 0)
