from django.test import TestCase
from django.contrib.sites.models import Site
from django.contrib.auth.models import User

from smbs_apps.smbs_user_posts.models import UserPostSettings, UserPost


class UserPostSettingsTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_create_settings(self):
        s = UserPostSettings.objects.create(site=self.site)
        self.assertTrue(s.comments_enabled)

    def test_get_default_tags_empty_when_no_settings(self):
        tags = UserPostSettings.get_default_tags()
        self.assertEqual(tags, [])

    def test_get_object_none_when_missing(self):
        self.assertIsNone(UserPostSettings.get_object())


class UserPostTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(username='poster', password='pass')

    def _make_post(self, **kwargs):
        defaults = dict(
            site=self.site,
            user=self.user,
            content='This is my post content.',
        )
        defaults.update(kwargs)
        return UserPost.objects.create(**defaults)

    def test_create_post(self):
        post = self._make_post()
        self.assertEqual(post.user, self.user)
        self.assertFalse(post.is_anonymous)

    def test_anonymous_post(self):
        post = self._make_post(is_anonymous=True)
        self.assertTrue(post.is_anonymous)

    def test_get_absolute_url(self):
        post = self._make_post()
        url = post.get_absolute_url()
        self.assertIn(str(post.id), url)

    def test_timestamps_set(self):
        post = self._make_post()
        self.assertIsNotNone(post.created)
        self.assertIsNotNone(post.updated)

    def test_post_with_title(self):
        post = self._make_post(title='My First Post')
        self.assertEqual(post.title, 'My First Post')

    def test_post_with_url(self):
        post = self._make_post(url='https://example.com/article')
        self.assertEqual(post.url, 'https://example.com/article')
