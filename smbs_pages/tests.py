from django.test import TestCase
from django.contrib.sites.models import Site
from django.core.files.uploadedfile import SimpleUploadedFile

from smbs_apps.smbs_pages.models import Page, media_upload_to, Media


class _MockMedia:
    def __init__(self, name=''):
        self.name = name
        self.file = None


class PageDepthTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def _make_page(self, slug, parent=None):
        return Page.objects.create(
            site=self.site,
            name=slug,
            slug=slug,
            parent=parent,
            active=True,
        )

    def test_root_page_saves(self):
        page = self._make_page('home')
        self.assertEqual(page.slug, 'home')

    def test_one_level_deep_saves(self):
        root = self._make_page('root')
        child = self._make_page('child', parent=root)
        self.assertEqual(child.parent, root)

    def test_two_levels_deep_saves(self):
        root = self._make_page('root')
        child = self._make_page('child', parent=root)
        grandchild = self._make_page('grandchild', parent=child)
        self.assertEqual(len(grandchild.get_all_parents()), 2)

    def test_three_levels_deep_raises(self):
        root = self._make_page('root')
        child = self._make_page('child', parent=root)
        grandchild = self._make_page('grandchild', parent=child)
        with self.assertRaises(Exception):
            self._make_page('great-grandchild', parent=grandchild)

    def test_get_all_parents_root_has_none(self):
        root = self._make_page('root2')
        self.assertEqual(root.get_all_parents(), [])

    def test_get_all_parents_returns_chain(self):
        root = self._make_page('p1')
        child = self._make_page('p2', parent=root)
        grandchild = self._make_page('p3', parent=child)
        parents = grandchild.get_all_parents()
        self.assertEqual(len(parents), 2)
        self.assertIn(root, parents)
        self.assertIn(child, parents)

    def test_str_returns_name(self):
        page = self._make_page('about')
        self.assertEqual(str(page), 'about')

    def test_has_child_pages(self):
        root = self._make_page('root3')
        self._make_page('child3', parent=root)
        self.assertTrue(root.has_child_pages())

    def test_no_child_pages(self):
        page = self._make_page('lone')
        self.assertFalse(page.has_child_pages())


class MediaUploadToTest(TestCase):
    def test_uses_instance_name_for_path(self):
        instance = _MockMedia(name='my banner')
        path = media_upload_to(instance, 'upload.jpg')
        self.assertIn('my-banner', path)
        self.assertTrue(path.startswith('page/media/'))
        self.assertTrue(path.endswith('.jpg'))

    def test_falls_back_to_filename_stem(self):
        instance = _MockMedia(name='')
        path = media_upload_to(instance, 'photo.png')
        self.assertIn('photo', path)

    def test_extension_preserved(self):
        instance = _MockMedia(name='doc')
        path = media_upload_to(instance, 'file.pdf')
        self.assertTrue(path.endswith('.pdf'))


class MediaTypeDetectionTest(TestCase):
    def _make_media(self, filename):
        f = SimpleUploadedFile(filename, b'data')
        media = Media(file=f)
        return media

    def test_image_type_detected(self):
        media = self._make_media('photo.jpg')
        media_type = media._guess_media_type()
        self.assertEqual(media_type, Media.IMAGE)

    def test_video_type_detected(self):
        media = self._make_media('clip.mp4')
        media_type = media._guess_media_type()
        self.assertEqual(media_type, Media.VIDEO)

    def test_audio_type_detected(self):
        media = self._make_media('track.mp3')
        media_type = media._guess_media_type()
        self.assertEqual(media_type, Media.AUDIO)

    def test_unknown_type_defaults_to_document(self):
        media = self._make_media('archive.xyz')
        media_type = media._guess_media_type()
        self.assertEqual(media_type, Media.DOCUMENT)

    def test_pdf_is_document(self):
        media = self._make_media('report.pdf')
        media_type = media._guess_media_type()
        self.assertEqual(media_type, Media.DOCUMENT)
