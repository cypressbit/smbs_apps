from django.test import TestCase
from django.contrib.sites.models import Site

from smbs_apps.smbs_blog.models import BlogSettings
from smbs_apps.smbs_blog.seo import (
    post_word_count,
    post_images,
    post_keywords,
    post_internal_links,
    post_external_links,
    run_seo_checks,
)


class _MockPost:
    """Minimal post stand-in for SEO function tests."""
    def __init__(self, content='', title='', description='', pk=1, cover_image=True):
        self.content = content
        self.title = title
        self.description = description
        self.pk = pk
        self.cover_image = cover_image


class BlogSettingsTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_get_enabled_checks_returns_class_default_when_no_db_settings(self):
        checks = BlogSettings.get_enabled_checks()
        self.assertEqual(checks, BlogSettings.SEO_CHECKS)

    def test_get_settings_returns_defaults_when_no_db_settings(self):
        settings = BlogSettings.get_settings()
        self.assertEqual(settings['word_count']['min_count'], BlogSettings.MIN_WORD_COUNT)
        self.assertEqual(settings['tags']['min_count'], BlogSettings.MIN_TAG_COUNT)
        self.assertEqual(settings['images']['min_count'], BlogSettings.MIN_IMAGE_COUNT)

    def test_create_settings(self):
        s = BlogSettings.objects.create(site=self.site)
        self.assertFalse(s.comments_enabled)

    def test_get_object_none_when_missing(self):
        self.assertIsNone(BlogSettings.get_object())


class PostWordCountTest(TestCase):
    def test_meets_minimum(self):
        words = ' '.join(['word'] * 500)
        post = _MockPost(content=f'<p>{words}</p>')
        result = post_word_count(post, min_count=500)
        self.assertTrue(result['success'])
        self.assertGreaterEqual(result['results'], 500)

    def test_below_minimum(self):
        post = _MockPost(content='<p>Too short</p>')
        result = post_word_count(post, min_count=500)
        self.assertFalse(result['success'])

    def test_strips_script_tags(self):
        post = _MockPost(content='<script>var x=1;</script><p>hello world</p>')
        result = post_word_count(post, min_count=1)
        self.assertTrue(result['success'])
        self.assertLessEqual(result['results'], 5)


class PostImagesTest(TestCase):
    def test_counts_cover_image(self):
        post = _MockPost(content='<p>No inline images</p>', cover_image=True)
        result = post_images(post, min_count=1)
        self.assertTrue(result['success'])

    def test_counts_inline_images(self):
        post = _MockPost(
            content='<img src="a.jpg"><img src="b.jpg">',
            cover_image=False,
        )
        result = post_images(post, min_count=2)
        self.assertTrue(result['success'])

    def test_fails_with_no_images(self):
        post = _MockPost(content='<p>No images</p>', cover_image=False)
        result = post_images(post, min_count=1)
        self.assertFalse(result['success'])


class PostKeywordsTest(TestCase):
    def test_finds_overlapping_keywords(self):
        post = _MockPost(
            content='<p>python django framework web</p>',
            title='Python django framework guide',
            description='A guide to python django web framework',
        )
        result = post_keywords(post, min_count=1)
        self.assertTrue(result['success'])

    def test_fails_with_no_overlap(self):
        post = _MockPost(
            content='<p>completely different words here</p>',
            title='Unique title text',
            description='Another unique description',
        )
        result = post_keywords(post, min_count=3)
        self.assertFalse(result['success'])


class PostLinksTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()
        self.site.domain = 'example.com'
        self.site.save()

    def test_internal_link_by_relative_path(self):
        post = _MockPost(content='<a href="/about/">About</a>')
        result = post_internal_links(post, min_count=1)
        self.assertTrue(result['success'])

    def test_internal_link_by_domain(self):
        post = _MockPost(content='<a href="http://example.com/page/">Page</a>')
        result = post_internal_links(post, min_count=1)
        self.assertTrue(result['success'])

    def test_external_link(self):
        post = _MockPost(content='<a href="https://google.com/">Google</a>')
        result = post_external_links(post, min_count=1)
        self.assertTrue(result['success'])

    def test_no_external_links_fails(self):
        post = _MockPost(content='<a href="/about/">Internal only</a>')
        result = post_external_links(post, min_count=1)
        self.assertFalse(result['success'])


class RunSeoChecksTest(TestCase):
    def test_passing_checks(self):
        words = ' '.join(['word'] * 600)
        post = _MockPost(
            content=f'<p>{words}</p>',
            cover_image=True,
        )
        settings = {'word_count': {'min_count': 500}}
        results, errors = run_seo_checks(['word_count'], settings, post)
        self.assertTrue(results['passed'])
        self.assertEqual(errors, [])

    def test_failing_check_produces_error(self):
        post = _MockPost(content='<p>Short</p>')
        settings = {'word_count': {'min_count': 500}}
        results, errors = run_seo_checks(['word_count'], settings, post)
        self.assertFalse(results['passed'])
        self.assertGreater(len(errors), 0)

    def test_empty_checks_list(self):
        post = _MockPost(content='')
        results, errors = run_seo_checks([], {}, post)
        self.assertTrue(results['passed'])
        self.assertEqual(errors, [])
