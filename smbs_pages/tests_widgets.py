"""Tests for the schema widget library and section patterns."""
import importlib.util
import io
import json
import re
import shutil
import tempfile
from unittest import skipUnless
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from smbs_apps.smbs_pages import documents, images, patterns, rendering, widgets
from smbs_apps.smbs_pages.models import Media


# Page documents need nh3 (rich text sanitizing); hosts that only use the
# legacy tree may not install it.
needs_nh3 = skipUnless(importlib.util.find_spec('nh3'), 'page documents need nh3')


def doc_with(*widget_nodes):
    return {'schema_version': 1, 'sections': [{
        'id': 'sec_test1', 'style': {}, 'rows': [{
            'id': 'row_test1', 'style': {}, 'columns': [{
                'id': 'col_test1', 'span': {'xs': 12}, 'valign': 'top', 'widgets': list(widget_nodes)}]}]}]}


def node(widget_type, props=None, node_id='w_test1'):
    return {'id': node_id, 'type': widget_type, 'props': props}


@needs_nh3
class WidgetLibraryTests(TestCase):

    def setUp(self):
        self.request = RequestFactory().get('/')

    def render(self, doc, edit=False):
        return str(rendering.render_document(doc, {'request': self.request}, edit=edit))

    def test_every_widget_default_validates_and_renders(self):
        registry = widgets.get_registry()
        self.assertGreaterEqual(len(registry), 25)
        for key, widget_class in registry.items():
            with self.subTest(widget=key):
                props = widget_class.clean_props(widget_class.defaults())
                doc, _ = documents.validate(doc_with(node(key, props)), allow_staff_widgets=True)
                for edit in (False, True):
                    html = self.render(doc, edit=edit)
                    self.assertNotIn('db-widget-error', html)
                    self.assertIn(f'db-widget-{key.replace("_", "-")}', html)

    def test_every_widget_describes_itself_as_json(self):
        for key, widget_class in widgets.get_registry().items():
            with self.subTest(widget=key):
                json.dumps(widget_class.json_schema())
                description = json.loads(json.dumps(widget_class.describe()))
                self.assertEqual(description['key'], key)
                self.assertTrue(description['name'])
                self.assertTrue(widget_class.template)

    def test_catalog_hides_staff_only_and_disabled_capabilities(self):
        keys = {entry['key'] for entry in widgets.catalog(capabilities={'forms'})}
        self.assertIn('contact_form', keys)
        self.assertNotIn('latest_posts', keys)
        self.assertNotIn('raw_html', keys)

    def test_text_is_escaped(self):
        doc, _ = documents.validate(doc_with(node('heading', {'text': '<script>alert(1)</script>'})))
        html = self.render(doc)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_video_embed_only_accepts_youtube_and_vimeo(self):
        widget_class = widgets.get_widget('video_embed')
        with self.assertRaises(Exception):
            widget_class.clean_props({'url': 'https://evil.example.com/watch?v=aqz-KE-bpKQ', 'title': 'x'})
        with self.assertRaises(Exception):
            widget_class.clean_props({'url': 'javascript:alert(1)', 'title': 'x'})
        props = widget_class.clean_props({'url': 'https://youtu.be/aqz-KE-bpKQ', 'title': 'Tour'})
        doc, _ = documents.validate(doc_with(node('video_embed', props)))
        self.assertIn('https://www.youtube-nocookie.com/embed/aqz-KE-bpKQ', self.render(doc))
        props = widget_class.clean_props({'url': 'https://vimeo.com/76979871', 'title': 'Tour'})
        doc, _ = documents.validate(doc_with(node('video_embed', props)))
        self.assertIn('https://player.vimeo.com/video/76979871', self.render(doc))

    def test_faq_accordion_ids_are_unique_per_node(self):
        items = [{'question': 'One?', 'answer': '<p>Yes.</p>'}, {'question': 'Two?', 'answer': '<p>No.</p>'}]
        doc, _ = documents.validate(doc_with(node('faq', {'items': items}, 'w_faq1'),
                                             node('faq', {'items': items}, 'w_faq2')))
        html = self.render(doc)
        ids = re.findall(r'\sid="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn('id="w_faq1-faq"', html)
        self.assertIn('id="w_faq2-faq"', html)

    def test_testimonials_sample_badge(self):
        items = [{'quote': 'Great!', 'name': 'Customer name'}]
        doc, _ = documents.validate(doc_with(node('testimonials', {'items': items, 'sample': True})))
        self.assertIn('Sample testimonial', self.render(doc))
        doc, _ = documents.validate(doc_with(node('testimonials', {'items': items, 'sample': False})))
        self.assertNotIn('Sample testimonial', self.render(doc))

    def test_testimonials_carousel_ids_are_unique(self):
        items = [{'quote': 'Great!', 'name': 'A'}, {'quote': 'Lovely!', 'name': 'B'}]
        doc, _ = documents.validate(doc_with(node('testimonials', {'items': items, 'layout': 'carousel'}, 'w_tst1'),
                                             node('testimonials', {'items': items, 'layout': 'carousel'}, 'w_tst2')))
        html = self.render(doc)
        self.assertIn('data-bs-target="#w_tst1-testimonials"', html)
        self.assertIn('data-bs-target="#w_tst2-testimonials"', html)

    def test_contact_form_renders_csrf_and_posts_to_contact_view(self):
        doc, _ = documents.validate(doc_with(node('contact_form', {'button_label': 'Send it'})))
        html = self.render(doc)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn('action="/form/contact/"', html)
        for field in ('name', 'email', 'phone', 'message'):
            self.assertIn(f'name="{field}"', html)
        self.assertIn('Send it', html)

    def test_latest_posts_hides_drafts_and_other_sites(self):
        from smbs_apps.smbs_blog.models import Post
        site = Site.objects.get_current()
        other_site = Site.objects.create(domain='other.example.com', name='Other')
        author = User.objects.create_user('author')
        now = timezone.now()

        def post(title, **kwargs):
            values = {'site': site, 'author': author, 'slug': title.lower().replace(' ', '-'), 'title': title,
                      'publish_date': now, 'language': 'en', 'content': '<p>Body</p>', 'description': 'About it',
                      'is_draft': False, **kwargs}
            return Post.objects.bulk_create([Post(**values)])[0]

        post('Published post')
        post('Older post', publish_date=now - timedelta(days=3))
        post('Draft post', is_draft=True)
        post('Other site post', site=other_site)
        doc, _ = documents.validate(doc_with(node('latest_posts', {'count': 3, 'layout': 'list'})))
        html = self.render(doc)
        self.assertIn('Published post', html)
        self.assertIn('Older post', html)
        self.assertLess(html.index('Published post'), html.index('Older post'))
        self.assertNotIn('Draft post', html)
        self.assertNotIn('Other site post', html)

    def test_raw_html_is_staff_only(self):
        doc = doc_with(node('raw_html', {'html': '<marquee>hi</marquee>'}))
        with self.assertRaises(documents.DocumentError):
            documents.validate(doc)
        cleaned, _ = documents.validate(doc, allow_staff_widgets=True)
        self.assertIn('<marquee>hi</marquee>', self.render(cleaned))

    def test_images_render_with_alt_and_unsplash_attribution(self):
        media = Media.objects.create(name='team', source=Media.UNSPLASH, remote_url='https://images.unsplash.com/photo-1',
                                     alt_text='A smiling baker',
                                     attribution={'name': 'Jane Doe', 'profile_url': 'https://unsplash.com/@jane'})
        members = [{'name': 'Ana', 'role': 'Owner', 'photo': {'media': media.id, 'alt': 'Ana in the bakery'}}]
        doc, _ = documents.validate(doc_with(node('team', {'members': members})))
        html = self.render(doc)
        self.assertIn('src="https://images.unsplash.com/photo-1?w=1440&amp;q=75&amp;auto=format"', html)
        self.assertIn('alt="Ana in the bakery"', html)
        self.assertIn('loading="lazy"', html)

        doc, _ = documents.validate(doc_with(node('image', {'image': {'media': media.id, 'alt': 'Bread'}})))
        html = self.render(doc)
        self.assertIn('Photo by <a href="https://unsplash.com/@jane?', html)
        self.assertIn('Unsplash</a>', html)

    def test_links_resolve(self):
        buttons = [{'label': 'Call', 'link': {'kind': 'tel', 'tel': '+1 (555) 555-0100'}, 'style': 'primary'},
                   {'label': 'Site', 'link': {'kind': 'url', 'url': 'https://example.com', 'new_tab': True},
                    'style': 'secondary'}]
        doc, _ = documents.validate(doc_with(node('button_group', {'buttons': buttons})))
        html = self.render(doc)
        self.assertIn('href="tel:+15555550100"', html)
        self.assertIn('href="https://example.com" target="_blank" rel="noopener"', html)

    def test_location_map_url_encodes_address(self):
        doc, _ = documents.validate(doc_with(node('location_map', {'address': '1 Main St & 2nd Ave, Austin TX'})))
        self.assertIn('maps?q=1+Main+St+%26+2nd+Ave%2C+Austin+TX&amp;output=embed', self.render(doc))


@needs_nh3
class PatternTests(TestCase):

    def test_patterns_load_with_metadata(self):
        listed = patterns.list_patterns()
        self.assertGreaterEqual(len(listed), 20)
        for pattern in listed:
            self.assertNotIn('section', pattern)
            self.assertTrue(pattern['name'] and pattern['description'] and pattern['ai_hint'])

    def test_every_pattern_instantiates_validates_and_renders(self):
        request = RequestFactory().get('/')
        for pattern in patterns.list_patterns():
            with self.subTest(pattern=pattern['key']):
                section = patterns.instantiate(pattern['key'])
                self.assertEqual(section['pattern'], pattern['key'])
                doc, _ = documents.validate({'schema_version': 1, 'sections': [section]})
                html = str(rendering.render_document(doc, {'request': request}))
                self.assertNotIn('db-widget-error', html)

    def test_instances_get_fresh_ids(self):
        first, second = patterns.instantiate('hero.centered'), patterns.instantiate('hero.centered')
        first_ids = {n['id'] for n, _ in documents.walk({'sections': [first]})}
        second_ids = {n['id'] for n, _ in documents.walk({'sections': [second]})}
        self.assertFalse(first_ids & second_ids)
        documents.validate({'schema_version': 1, 'sections': [first, second]})

    def test_capability_filter(self):
        keys = {p['key'] for p in patterns.list_patterns(capabilities=set())}
        self.assertNotIn('contact.split_map', keys)
        self.assertNotIn('blog.latest', keys)
        self.assertIn('hero.centered', keys)
        keys = {p['key'] for p in patterns.list_patterns(capabilities={'forms'})}
        self.assertIn('contact.split_map', keys)

    def test_unknown_pattern(self):
        with self.assertRaises(patterns.UnknownPattern):
            patterns.instantiate('nope.nothing')

    def test_catalog_includes_sections(self):
        entries = patterns.catalog(capabilities={'forms', 'blog'})
        self.assertTrue(all('section' in entry for entry in entries))
        json.dumps(entries)


class FieldMarkerTests(TestCase):
    """Edit mode marks widget text for in-place editing; the published HTML carries no markers."""

    def test_markers_only_in_edit_mode(self):
        for pattern in patterns.list_patterns():
            section = patterns.instantiate(pattern['key'])
            doc = {'schema_version': 1, 'sections': [section]}
            published = str(rendering.render_document(doc))
            self.assertNotIn('data-db-field', published, pattern['key'])
            edited = str(rendering.render_document(doc, edit=True))
            for path in re.findall(r'data-db-field="([^"]+)"', edited):
                self.assertTrue(all(part.isidentifier() or part.isdigit() for part in path.split('.')), path)

    def test_marker_paths_resolve_to_text(self):
        hero = {'id': 'w_1', 'type': 'hero', 'props': widgets.get_widget('hero').defaults()}
        hero['props']['variant'] = 'split'
        features = {'id': 'w_2', 'type': 'feature_grid', 'props': widgets.get_widget('feature_grid').defaults()}
        doc = {'schema_version': 1, 'sections': [{'id': 's_1', 'style': {}, 'rows': [{'id': 'r_1', 'style': {}, 'columns': [
            {'id': 'c_1', 'span': {'xs': 12}, 'valign': 'top', 'widgets': [hero, features]}]}]}]}
        html = str(rendering.render_document(doc, edit=True))
        self.assertIn('data-db-field="heading"', html)
        self.assertIn('data-db-field="buttons.0.label"', html)
        self.assertIn('data-db-field="items.0.title"', html)
        for widget in (hero, features):
            fragment = str(rendering.Renderer(edit=True).widget(widget))
            for path in re.findall(r'data-db-field="([^"]+)"', fragment):
                value = widget['props']
                for part in path.split('.'):
                    value = value[int(part)] if part.isdigit() else value[part]
                self.assertIsInstance(value, str, path)


def image_bytes(size, image_format='JPEG', mode='RGB', **save):
    from PIL import Image
    buffer = io.BytesIO()
    Image.new(mode, size, 'red' if mode == 'RGB' else (255, 0, 0, 128)).save(buffer, image_format, **save)
    return buffer.getvalue()


@needs_nh3
class ResponsiveImageTests(TestCase):

    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root)
        settings = override_settings(MEDIA_ROOT=self.media_root, MEDIA_URL='/media/')
        settings.enable()
        self.addCleanup(settings.disable)

    def upload(self, data, filename='photo.jpg'):
        media = Media(name=filename.split('.')[0], media_type=Media.IMAGE, alt_text='A photo')
        media.file.save(filename, ContentFile(data), save=False)
        media.save()
        return media

    def opened(self, name):
        from PIL import Image
        with Image.open(f'{self.media_root}/{name}') as image:
            return image.format, image.size, image.mode

    def render(self, doc, edit=False):
        return str(rendering.render_document(doc, {'request': RequestFactory().get('/')}, edit=edit))

    def test_uploads_get_smaller_webp_copies_the_right_way_up(self):
        from PIL import Image
        exif = Image.Exif()
        exif[0x0112] = 6  # taken with the phone turned: shown rotated 90°
        media = self.upload(image_bytes((3000, 2000), exif=exif.tobytes()))
        widths = media.variants['widths']
        self.assertEqual(media.variants['source'], media.file.name)
        self.assertEqual(sorted(widths, key=int), ['480', '960', '1440', '2000'])
        self.assertEqual(self.opened(widths['2000']), ('WEBP', (2000, 3000), 'RGB'))
        self.assertEqual(self.opened(widths['480'])[1], (480, 720))
        saved = Media.objects.get(pk=media.pk)
        self.assertEqual((saved.variants, saved.width, saved.height), (media.variants, 2000, 3000))
        # The browser picks from the copies; the original is never sent.
        self.assertEqual(images.src(media), f'/media/{widths["1440"]}')
        self.assertEqual(images.src(media, 600), f'/media/{widths["960"]}')
        self.assertEqual(images.src(media, 5000), f'/media/{widths["2000"]}')
        self.assertTrue(images.srcset(media).startswith(f'/media/{widths["480"]} 480w, '))

    def test_small_images_are_never_enlarged_and_keep_transparency(self):
        media = self.upload(image_bytes((300, 100), 'PNG', mode='RGBA'), 'logo.png')
        self.assertEqual(list(media.variants['widths']), ['300'])
        self.assertEqual(self.opened(media.variants['widths']['300']), ('WEBP', (300, 100), 'RGBA'))

    def test_a_new_file_replaces_the_copies(self):
        media = self.upload(image_bytes((1000, 500)))
        old = set(media.variants['widths'].values())
        media.file.save('other.jpg', ContentFile(image_bytes((600, 300))), save=False)
        media.save()
        self.assertEqual(sorted(media.variants['widths'], key=int), ['480', '600'])
        for name in old - set(media.variants['widths'].values()):
            self.assertFalse(media.file.storage.exists(name))

    def test_files_without_copies_are_served_as_they_are(self):
        from PIL import Image
        frames = [Image.new('RGB', (800, 600), color) for color in ('red', 'blue')]
        buffer = io.BytesIO()
        frames[0].save(buffer, 'GIF', save_all=True, append_images=frames[1:])
        animated = self.upload(buffer.getvalue(), 'dance.gif')
        with self.assertLogs('smbs_apps.smbs_pages.images', 'ERROR'):
            broken = self.upload(b'not an image', 'broken.jpg')  # saving still works
        for media in (animated, broken):
            self.assertEqual(media.variants['widths'], {})
            self.assertEqual(images.srcset(media), '')
            self.assertEqual(images.src(media), media.url)
        doc, _ = documents.validate(doc_with(node('image', {'image': {'media': animated.id, 'alt': 'Dancing'}})))
        html = self.render(doc)
        self.assertIn(f'src="{animated.url}"', html)
        self.assertNotIn('srcset', html)

    def test_unsplash_sizes_come_from_the_url(self):
        media = Media.objects.create(source=Media.UNSPLASH, width=1200, height=800,
                                     remote_url='https://images.unsplash.com/photo-1?ixid=abc&fm=jpg&q=80&w=1080')
        self.assertEqual([w for _, w in images.candidates(media)], [480, 960])
        self.assertEqual(images.src(media), 'https://images.unsplash.com/photo-1?ixid=abc&fm=jpg&w=960&q=75&auto=format')

    def test_widgets_and_backgrounds_use_the_copies(self):
        media = self.upload(image_bytes((2400, 1600)))
        widths = media.variants['widths']
        doc, _ = documents.validate(doc_with(node('content_split', {
            'heading': 'Fresh bread', 'image': {'media': media.id, 'alt': 'Bread'}})))
        doc['sections'][0]['style'] = {'background': {'image': {'media': media.id}}}
        html = self.render(doc)
        self.assertIn(f'src="/media/{widths["1440"]}" srcset="/media/{widths["480"]} 480w,', html)
        self.assertIn('sizes="(min-width: 1400px) 660px, (min-width: 768px) 50vw, 100vw" width="2400" height="1600"', html)
        self.assertIn('db-bg-responsive', html)
        self.assertIn(f"--db-bg-sm:url('/media/{widths['960']}')", html)
        self.assertIn(f"--db-bg-lg:url('/media/{widths['2000']}')", html)

    def test_gallery_photos_open_in_the_lightbox_but_not_in_the_editor(self):
        media = self.upload(image_bytes((2400, 1600)))
        doc, _ = documents.validate(doc_with(node('gallery', {
            'columns': 3, 'images': [{'image': {'media': media.id, 'alt': 'Cakes'}, 'caption': 'Cakes'}] * 2})))
        html = self.render(doc)
        self.assertIn(f'<a href="/media/{media.variants["widths"]["2000"]}" class="db-lightbox-link', html)
        self.assertIn('sizes="(min-width: 1400px) 440px, (min-width: 768px) 33vw, 50vw"', html)
        self.assertNotIn('db-lightbox-link', self.render(doc, edit=True))

    def test_backfill_command(self):
        media = self.upload(image_bytes((1000, 500)))
        Media.objects.filter(pk=media.pk).update(variants={})
        call_command('build_image_variants', stdout=io.StringIO())
        self.assertEqual(sorted(Media.objects.get(pk=media.pk).variants['widths'], key=int), ['480', '960', '1000'])
        out = io.StringIO()
        call_command('build_image_variants', stdout=out)
        self.assertIn('0 image(s)', out.getvalue())
