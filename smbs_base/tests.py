from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.sites.models import Site
from django.core.files.uploadedfile import SimpleUploadedFile

from smbs_apps.smbs_base.models import (
    validate_image_extension,
    BaseSettings,
    ViewMetadata,
    ObjectMetadata,
)


def _file(name):
    return SimpleUploadedFile(name, b'data')


class ValidateImageExtensionTest(TestCase):
    def test_png_passes(self):
        validate_image_extension(_file('logo.png'))

    def test_jpg_passes(self):
        validate_image_extension(_file('logo.jpg'))

    def test_jpeg_passes(self):
        validate_image_extension(_file('logo.jpeg'))

    def test_svg_passes(self):
        validate_image_extension(_file('logo.svg'))

    def test_gif_raises(self):
        with self.assertRaises(ValidationError):
            validate_image_extension(_file('logo.gif'))

    def test_webp_raises(self):
        with self.assertRaises(ValidationError):
            validate_image_extension(_file('logo.webp'))


class BaseSettingsTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_get_object_returns_none_when_missing(self):
        self.assertIsNone(BaseSettings.get_object())

    def test_get_object_returns_existing(self):
        s = BaseSettings.objects.create(site=self.site)
        self.assertEqual(BaseSettings.get_object(), s)

    def test_clean_blocks_duplicate_per_site(self):
        BaseSettings.objects.create(site=self.site)
        duplicate = BaseSettings(site=self.site)
        with self.assertRaises(ValidationError):
            duplicate.clean()

    def test_navbar_type_default(self):
        s = BaseSettings.objects.create(site=self.site)
        self.assertEqual(s.navbar_type, BaseSettings.NAVBAR_LIGHT)

    def test_email_use_tls_default_false(self):
        s = BaseSettings.objects.create(site=self.site)
        self.assertFalse(s.email_use_tls)


class ViewMetadataTest(TestCase):
    def test_create_with_view_name(self):
        vm = ViewMetadata.objects.create(view='home')
        self.assertEqual(vm.view, 'home')

    def test_view_unique(self):
        ViewMetadata.objects.create(view='home')
        with self.assertRaises(Exception):
            ViewMetadata.objects.create(view='home')


class ObjectMetadataTest(TestCase):
    def test_get_image_url_without_image(self):
        om = ObjectMetadata.objects.create()
        self.assertIsNone(om.get_image_url())

    def test_get_site_name(self):
        site = Site.objects.get_current()
        self.assertEqual(ObjectMetadata.get_site_name(), site.name)

    def test_title_and_description_stored(self):
        om = ObjectMetadata.objects.create(title='Test', description='Desc')
        self.assertEqual(om.title, 'Test')
        self.assertEqual(om.description, 'Desc')
