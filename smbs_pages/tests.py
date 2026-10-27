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


# ---------------------------------------------------------------------------
# Page documents (smbs_pages v2)
# ---------------------------------------------------------------------------

import copy  # noqa: E402
import importlib.util  # noqa: E402
from unittest import skipUnless  # noqa: E402

from django.urls import reverse  # noqa: E402

from django.contrib.auth.models import User  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.test import SimpleTestCase  # noqa: E402

from smbs_apps.smbs_pages import documents, fields, services  # noqa: E402
from smbs_apps.smbs_pages.models import Container, Row, Column, Widget, PageRevision, SiteChrome  # noqa: E402
from smbs_apps.smbs_pages.widgets import catalog, get_widget, legacy_widget_choices  # noqa: E402


# Page documents need nh3 (rich text sanitizing); hosts that only use the
# legacy tree may not install it.
needs_nh3 = skipUnless(importlib.util.find_spec('nh3'), 'page documents need nh3')


def url(page):
    return page.get_absolute_url()


def home_url():
    return reverse('smbs_pages:page-detail')


def heading(text='Hello', node_id='w_aaaa1111', level=1):
    return {'id': node_id, 'type': 'heading', 'props': {'text': text, 'level': level, 'eyebrow': '', 'size': 'default'}}


def doc_with(*widgets, section_id='sec_aaaa1111'):
    return {'schema_version': 1, 'sections': [{
        'id': section_id, 'style': {},
        'rows': [{'id': 'row_aaaa1111', 'columns': [{
            'id': 'col_aaaa1111', 'span': {'xs': 12}, 'widgets': list(widgets)}]}],
    }]}


@needs_nh3
class FieldTests(SimpleTestCase):

    def clean(self, field, value, **ctx):
        return field.clean(value, fields.CleanContext(**ctx))

    def test_text_collapses_whitespace_and_limits_length(self):
        self.assertEqual(self.clean(fields.Text(), '  a   b \n c '), 'a b c')
        self.assertEqual(self.clean(fields.Text(multiline=True), ' a\nb '), 'a\nb')
        with self.assertRaises(fields.FieldError):
            self.clean(fields.Text(max_length=3), 'abcd')
        with self.assertRaises(fields.FieldError):
            self.clean(fields.Text(), '')

    def test_rich_text_is_sanitized(self):
        html = '<p onclick="x()">Hi <script>alert(1)</script><a href="javascript:alert(1)">x</a> <strong>b</strong></p>'
        cleaned = self.clean(fields.RichText(), html)
        self.assertNotIn('script', cleaned)
        self.assertNotIn('onclick', cleaned)
        self.assertNotIn('javascript', cleaned)
        self.assertIn('<strong>b</strong>', cleaned)

    def test_image_requires_alt_text(self):
        with self.assertRaises(fields.FieldError):
            self.clean(fields.Image(), {'media': 3, 'alt': ' '})
        self.assertEqual(self.clean(fields.Image(), {'media': 3, 'alt': 'A cake'}), {'media': 3, 'alt': 'A cake'})

    def test_media_keys_only_in_spec_mode(self):
        with self.assertRaises(fields.FieldError):
            self.clean(fields.Image(), {'media': 'hero', 'alt': 'x'})
        self.assertEqual(self.clean(fields.Image(), {'media': 'hero', 'alt': 'x'}, allow_keys=True)['media'], 'hero')

    def test_link_rejects_script_urls(self):
        for bad in ({'kind': 'url', 'url': 'javascript:alert(1)'}, {'kind': 'url', 'url': '//evil.com'},
                    {'kind': 'email', 'email': 'nope'}, {'kind': 'nope'}):
            with self.subTest(bad=bad), self.assertRaises(fields.FieldError):
                self.clean(fields.Link(), bad)
        self.assertEqual(self.clean(fields.Link(), {'kind': 'tel', 'tel': '+1 (512) 555-0100', 'new_tab': True}),
                         {'kind': 'tel', 'tel': '+1 (512) 555-0100', 'new_tab': True})

    def test_icon_must_exist(self):
        self.assertEqual(self.clean(fields.Icon(), 'telephone'), 'telephone')
        with self.assertRaises(fields.FieldError):
            self.clean(fields.Icon(), 'not-a-real-icon-name')

    def test_repeater_bounds_and_schema_errors_are_collected(self):
        field = fields.Repeater(fields.Schema(title=fields.Text(max_length=5)), min_items=1, max_items=2)
        with self.assertRaises(fields.FieldError):
            self.clean(field, [])
        with self.assertRaises(fields.FieldErrors) as cm:
            self.clean(field, [{'title': 'toolong'}, {'title': ''}])
        self.assertEqual([e.path for e in cm.exception.errors], ['0.title', '1.title'])

    def test_schema_rejects_unknown_keys_and_has_json_schema(self):
        schema = fields.Schema(a=fields.Text(), b=fields.Number(required=False, min_value=1))
        with self.assertRaises(fields.FieldError):
            self.clean(schema, {'a': 'x', 'zzz': 1})
        json_schema = schema.value_schema()
        self.assertEqual(json_schema['required'], ['a'])
        self.assertFalse(json_schema['additionalProperties'])

    def test_map_references(self):
        schema = fields.Schema(img=fields.Image(required=False), link=fields.Link(required=False))
        value = {'img': {'media': 'hero', 'alt': 'x'}, 'link': {'kind': 'page', 'page': 'about'}}
        mapped = schema.map_references(value, lambda kind, ref: f'{kind}:{ref}')
        self.assertEqual(mapped['img']['media'], 'media:hero')
        self.assertEqual(mapped['link']['page'], 'page:about')


@needs_nh3
class WidgetRegistryTests(TestCase):

    def test_schema_and_legacy_widgets_are_discovered(self):
        keys = {item['key'] for item in catalog()}
        self.assertTrue({'heading', 'rich_text', 'image', 'button_group'} <= keys)
        self.assertIn('smbs_apps.smbs_pages.smbs_widgets.headline', dict(legacy_widget_choices()))
        legacy = get_widget('smbs_apps.smbs_pages.smbs_widgets.headline')
        self.assertTrue(legacy.staff_only)
        self.assertIs(legacy, get_widget('smbs_apps.smbs_pages.smbs_widgets.headline'))

    def test_defaults_are_valid(self):
        for key in ('heading', 'rich_text', 'image', 'button_group'):
            widget = get_widget(key)
            self.assertEqual(widget.clean_props(widget.defaults()), widget.defaults())


@needs_nh3
class DocumentValidationTests(TestCase):

    def test_valid_document(self):
        cleaned, refs = documents.validate(doc_with(heading()))
        self.assertEqual(cleaned['sections'][0]['rows'][0]['columns'][0]['widgets'][0]['props']['text'], 'Hello')
        self.assertEqual(cleaned['sections'][0]['style']['width'], 'contained')

    def test_errors_are_reported_with_paths(self):
        bad = doc_with({'id': 'w_aaaa1111', 'type': 'nope', 'props': {}},
                       {'id': 'w_aaaa1111', 'type': 'heading', 'props': {'text': ''}})
        with self.assertRaises(documents.DocumentError) as cm:
            documents.validate(bad)
        messages = ' '.join(e['message'] for e in cm.exception.errors)
        self.assertIn("Unknown widget type 'nope'", messages)
        self.assertIn('Duplicate node id', messages)
        self.assertIn('sections.0.rows.0.columns.0.widgets.1.props.text',
                      [e['path'] for e in cm.exception.errors])

    def test_assign_ids(self):
        doc = {'sections': [{'rows': [{'columns': [{'widgets': [{'type': 'heading'}]}]}]}]}
        cleaned, _ = documents.validate(doc, assign_ids=True)
        ids = [node['id'] for node, _ in documents.walk(cleaned)]
        self.assertEqual(len(set(ids)), 4)
        self.assertTrue(all(documents.NODE_ID.match(i) for i in ids))

    def test_staff_only_widgets(self):
        doc = doc_with({'id': 'w_aaaa1111', 'type': 'smbs_apps.smbs_pages.smbs_widgets.html', 'props': {'content': '<b>x</b>'}})
        with self.assertRaises(documents.DocumentError):
            documents.validate(doc)
        documents.validate(doc, allow_staff_widgets=True)

    def test_missing_media_reference(self):
        doc = doc_with({'id': 'w_aaaa1111', 'type': 'image', 'props': {'image': {'media': 999999, 'alt': 'x'}}})
        with self.assertRaises(documents.DocumentError) as cm:
            documents.validate(doc)
        self.assertIn('Media 999999 does not exist.', str(cm.exception))

    def test_section_css_cannot_close_style_tag(self):
        doc = doc_with(heading())
        doc['sections'][0]['style'] = {'css': '</style><script>x</script>'}
        with self.assertRaises(documents.DocumentError):
            documents.validate(doc)


@needs_nh3
class OperationTests(SimpleTestCase):

    def test_insert_widget_uses_defaults(self):
        doc = documents.apply_ops(doc_with(), [{'op': 'insert_widget', 'column_id': 'col_aaaa1111', 'widget': {'type': 'heading'}}])
        widget = doc['sections'][0]['rows'][0]['columns'][0]['widgets'][0]
        self.assertEqual(widget['props']['text'], 'Your heading')
        self.assertTrue(widget['id'].startswith('w_'))

    def test_move_delete_duplicate_update(self):
        doc = doc_with(heading('A', 'w_aaaa0001'), heading('B', 'w_aaaa0002'))
        doc = documents.apply_ops(doc, [
            {'op': 'move_node', 'node_id': 'w_aaaa0002', 'parent_id': 'col_aaaa1111', 'index': 0},
            {'op': 'duplicate_node', 'node_id': 'w_aaaa0001'},
            {'op': 'update_props', 'node_id': 'w_aaaa0002', 'props': {'text': 'B2'}},
            {'op': 'delete_node', 'node_id': 'w_aaaa0001'},
        ])
        widgets = doc['sections'][0]['rows'][0]['columns'][0]['widgets']
        self.assertEqual([w['props']['text'] for w in widgets], ['B2', 'A'])
        self.assertNotEqual(widgets[1]['id'], 'w_aaaa0001')

    def test_moving_into_wrong_parent_fails(self):
        with self.assertRaises(documents.OperationError):
            documents.apply_ops(doc_with(heading()), [{'op': 'move_node', 'node_id': 'w_aaaa1111', 'parent_id': 'root'}])

    def test_set_columns_keeps_widgets(self):
        doc = documents.apply_ops(doc_with(heading()), [
            {'op': 'set_columns', 'row_id': 'row_aaaa1111', 'spans': [{'xs': 12, 'md': 6}, {'xs': 12, 'md': 6}]},
        ])
        columns = doc['sections'][0]['rows'][0]['columns']
        self.assertEqual(len(columns), 2)
        doc = documents.apply_ops(doc, [
            {'op': 'insert_widget', 'column_id': columns[1]['id'], 'widget': {'type': 'rich_text'}},
            {'op': 'set_columns', 'row_id': 'row_aaaa1111', 'spans': [{'xs': 12}]},
        ])
        self.assertEqual([w['type'] for w in doc['sections'][0]['rows'][0]['columns'][0]['widgets']],
                         ['heading', 'rich_text'])

    def test_unknown_op(self):
        with self.assertRaises(documents.OperationError):
            documents.apply_ops(doc_with(), [{'op': 'explode'}])


@needs_nh3
class PublishingTests(TestCase):

    def setUp(self):
        self.site = Site.objects.get_current()
        self.page = Page.objects.create(site=self.site, name='About', slug='about', active=True)

    def test_save_draft_and_conflicts(self):
        version = services.save_draft(self.page, doc_with(heading('One')))
        self.assertEqual(version, 1)
        self.assertEqual(self.page.content_mode, Page.ContentMode.LEGACY)
        with self.assertRaises(services.DraftConflict):
            services.save_draft(self.page, doc_with(heading('Two')), expected_version=0)
        self.assertEqual(services.save_draft(self.page, doc_with(heading('Two')), expected_version=1), 2)

    def test_publish_and_restore(self):
        services.save_draft(self.page, doc_with(heading('One')))
        first = services.publish_page(self.page, note='first')
        services.save_draft(self.page, doc_with(heading('Two')))
        services.publish_page(self.page)
        self.page.refresh_from_db()
        self.assertEqual(self.page.content_mode, Page.ContentMode.DOCUMENT)
        self.assertEqual(self.page.published_revision.number, 2)
        restored = services.restore_revision(self.page, first.number)
        self.assertEqual(restored.number, 3)
        self.assertEqual(restored.document, first.document)
        self.page.refresh_from_db()
        self.assertEqual(self.page.draft, first.document)
        self.assertEqual(PageRevision.objects.filter(page=self.page).count(), 3)

    def test_preview_tokens_are_per_page(self):
        other = Page.objects.create(site=self.site, name='Other', slug='other')
        token = services.preview_token(self.page)
        self.assertTrue(services.check_preview_token(token, self.page))
        self.assertFalse(services.check_preview_token(token, other))
        self.assertFalse(services.check_preview_token(token + 'x', self.page))


@needs_nh3
class PageViewTests(TestCase):

    def setUp(self):
        self.site = Site.objects.get_current()

    def legacy_page(self, slug='legacy'):
        page = Page.objects.create(site=Site.objects.get_current(), name='Legacy', slug=slug, active=True)
        container = Container.objects.create(name='c')
        container.page.add(page)
        row = Row.objects.create(name='r')
        row.container.add(container)
        column = Column.objects.create(name='col', width=6)
        column.row.add(row)
        widget = Widget.objects.create(type='smbs_apps.smbs_pages.smbs_widgets.headline', content='Legacy title',
                                       custom_classes='big', options={'headline_type': 'h2'})
        widget.column.add(column)
        return page

    def test_legacy_page_renders_as_before(self):
        page = self.legacy_page()
        response = self.client.get(url(page))
        self.assertContains(response, '<h2 class="big">Legacy title</h2>', html=True)
        self.assertContains(response, 'class="col-md-6 ')
        self.assertNotContains(response, 'db-section')

    def test_document_page(self):
        page = Page.objects.create(site=self.site, name='Doc', slug='doc', active=True)
        services.save_draft(page, doc_with(heading('Published title')))
        self.assertEqual(self.client.get(url(page)).status_code, 200)  # legacy mode, empty tree
        services.publish_page(page)
        services.save_draft(page, doc_with(heading('Draft title')))
        response = self.client.get(url(page))
        self.assertContains(response, 'Published title')
        self.assertNotContains(response, 'Draft title')
        self.assertNotContains(response, 'data-db-node')
        preview = self.client.get(f'{url(page)}?preview={services.preview_token(page)}')
        self.assertContains(preview, 'Draft title')
        self.assertContains(preview, 'noindex')
        self.assertContains(self.client.get(f'{url(page)}?preview=bogus'), 'Published title')

    def test_unpublished_document_page_is_404(self):
        page = Page.objects.create(site=self.site, name='New', slug='new', active=True, content_mode=Page.ContentMode.DOCUMENT)
        self.assertEqual(self.client.get(url(page)).status_code, 404)

    def test_legacy_page_preview_shows_converted_draft(self):
        page = self.legacy_page()
        services.save_draft(page, doc_with(heading('Converted')))
        self.assertContains(self.client.get(url(page)), 'Legacy title')
        self.assertContains(self.client.get(f'{url(page)}?preview={services.preview_token(page)}'), 'Converted')

    def test_chrome_replaces_navbar_and_footer(self):
        page = Page.objects.create(site=self.site, name='Doc', slug='doc', active=True)
        services.save_draft(page, doc_with(heading('Body')))
        services.publish_page(page)
        chrome = SiteChrome.objects.create(site=self.site, draft={'header': doc_with(heading('Site header')),
                                                                  'footer': doc_with(heading('Site footer'))})
        self.assertNotContains(self.client.get(url(page)), 'Site header')
        services.publish_chrome(chrome)
        response = self.client.get(url(page))
        self.assertContains(response, 'db-chrome-header')
        self.assertContains(response, 'Site footer')


SPEC = {
    'schema_version': 1,
    'site': {'name': "Rosa's Bakery"},
    'theme': {'preset': 'warm'},
    'media': [{'key': 'bread', 'source': 'unsplash', 'remote_url': 'https://images.unsplash.com/photo-1?w=1600',
               'alt_text': 'Fresh loaves', 'attribution': {'name': 'Jane Doe', 'profile_url': 'https://unsplash.com/@jane'}}],
    'pages': [
        {'key': 'home', 'name': 'Home', 'slug': None, 'navigation_order': 0, 'metadata': {'title': "Rosa's Bakery"},
         'document': {'sections': [{'rows': [{'columns': [{'widgets': [
             {'type': 'heading', 'props': {'text': 'Fresh bread daily', 'level': 1, 'eyebrow': '', 'size': 'display'}},
             {'type': 'image', 'props': {'image': {'media': 'bread', 'alt': 'Fresh loaves'}, 'caption': '',
                                         'rounded': True, 'aspect': 'natural', 'link': {'kind': 'page', 'page': 'about'}}},
         ]}]}]}]}},
        {'key': 'about', 'name': 'About', 'slug': 'about', 'navigation_order': 1,
         'document': {'sections': [{'rows': [{'columns': [{'widgets': [{'type': 'rich_text'}]}]}]}]}},
    ],
    'chrome': {'footer': {'sections': [{'rows': [{'columns': [{'widgets': [{'type': 'rich_text', 'props': {'html': '<p>© Rosa</p>', 'lead': False}}]}]}]}]}},
}


@needs_nh3
class SiteSpecTests(TestCase):

    def test_spec_validation_errors(self):
        bad = copy.deepcopy(SPEC)
        bad['pages'][1]['slug'] = None
        bad['pages'][0]['document']['sections'][0]['rows'][0]['columns'][0]['widgets'][1]['props']['image']['media'] = 'nope'
        with self.assertRaises(documents.DocumentError) as cm:
            documents.validate_spec(bad)
        message = str(cm.exception)
        self.assertIn('Duplicate slug None', message)
        self.assertIn("Unknown media key 'nope'", message)

    def test_materialize_publishes_a_site(self):
        themes = []
        result = documents.materialize(SPEC, theme_handler=themes.append)
        self.assertEqual(themes, [{'preset': 'warm'}])
        self.assertEqual(Site.objects.get_current().name, "Rosa's Bakery")
        home = Page.objects.get(pk=result['pages']['home'])
        self.assertTrue(home.is_document)
        image = home.published_revision.document['sections'][0]['rows'][0]['columns'][0]['widgets'][1]['props']
        self.assertEqual(image['image']['media'], result['media']['bread'])
        self.assertEqual(image['link']['page'], result['pages']['about'])
        response = self.client.get(home_url())
        self.assertContains(response, 'Fresh bread daily')
        self.assertContains(response, 'https://images.unsplash.com/photo-1?w=1440&amp;q=75&amp;auto=format')
        self.assertContains(response, 'Photo by <a href="https://unsplash.com/@jane?')
        self.assertContains(response, f'href="{url(Page.objects.get(slug="about"))}"')
        self.assertContains(response, '© Rosa')
        self.assertEqual(home.metadata.title, "Rosa's Bakery")

    def test_materialize_is_idempotent_by_slug(self):
        first = documents.materialize(SPEC)
        second = documents.materialize(SPEC)
        self.assertEqual(first['pages'], second['pages'])
        self.assertEqual(first['media'], second['media'])
        self.assertEqual(Page.objects.count(), 2)
        self.assertEqual(Page.objects.get(slug=None).revisions.count(), 2)

    def test_materialize_without_publishing_keeps_legacy_pages_live(self):
        legacy = PageViewTests.legacy_page(self, slug='about')
        documents.materialize(SPEC, publish=False)
        legacy.refresh_from_db()
        self.assertEqual(legacy.content_mode, Page.ContentMode.LEGACY)
        self.assertTrue(legacy.draft['sections'])
        self.assertContains(self.client.get(url(legacy)), 'Legacy title')

    def test_export_round_trip(self):
        documents.materialize(SPEC)
        exported = documents.export()
        cleaned = documents.validate_spec(exported)
        self.assertEqual({p['slug'] for p in cleaned['pages']}, {None, 'about'})
        self.assertEqual(len(exported['media']), 1)
        self.assertTrue(exported['media'][0]['key'].startswith('media-'))


@needs_nh3
class ConvertCommandTests(TestCase):

    def test_convert_then_publish(self):
        page = PageViewTests.legacy_page(self)
        call_command('pages_convert', page=[page.pk], stdout=open('/dev/null', 'w'))
        page.refresh_from_db()
        self.assertEqual(page.content_mode, Page.ContentMode.LEGACY)
        widget = page.draft['sections'][0]['rows'][0]['columns'][0]['widgets'][0]
        self.assertEqual(widget['type'], 'smbs_apps.smbs_pages.smbs_widgets.headline')
        self.assertEqual(widget['props']['content'], 'Legacy title')
        call_command('pages_convert', page=[page.pk], publish=True, stdout=open('/dev/null', 'w'))
        page.refresh_from_db()
        self.assertTrue(page.is_document)
        response = self.client.get(url(page))
        self.assertContains(response, '<h2 class="big">Legacy title</h2>', html=True)
        self.assertContains(response, 'col-md-6')
