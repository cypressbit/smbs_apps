"""
Page documents and SiteSpecs: the one content format shared by the AI, the
visual editor and the renderer.

A **PageDocument** is a page's content tree as JSON:

    {"schema_version": 1, "sections": [
      {"id": "sec_7f3a", "pattern": "hero.split", "anchor": "top",
       "style": {"width": "contained", "padding_y": "lg", "background": {"color": "surface"}, "theme": "light"},
       "rows": [
         {"id": "row_19c2", "style": {"gap": "md", "align": "center"}, "columns": [
           {"id": "col_a1b2", "span": {"xs": 12, "md": 6}, "valign": "center", "widgets": [
             {"id": "w_51b0", "type": "heading", "props": {"text": "Fresh bread daily", "level": 1}}
           ]}]}]}]}

Widget `props` are validated by each widget's schema (see widgets.py,
fields.py). Media and page references are ids, or string keys inside a
SiteSpec.

A **SiteSpec** describes a whole site: pages (each with a document), the
header/footer chrome, media to create, and theme tokens. The AI produces one;
`materialize()` applies it to the database and `export()` reads it back.

This module must not import models at import time (models import it).
"""
import copy
import re
import secrets

from django.db import transaction

from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import get_widget


SCHEMA_VERSION = 1
NODE_ID_PREFIX = {'section': 'sec', 'row': 'row', 'column': 'col', 'widget': 'w'}
NODE_ID = re.compile(r'^[a-z]{1,4}_[A-Za-z0-9]{4,32}$')
CSS_CLASSES = re.compile(r'^[A-Za-z0-9 _-]*$')


def empty_document():
    return {'schema_version': SCHEMA_VERSION, 'sections': []}


def empty_chrome():
    return {'header': empty_document(), 'footer': empty_document()}


def new_id(kind):
    return f'{NODE_ID_PREFIX[kind]}_{secrets.token_hex(4)}'


class DocumentError(Exception):
    """Validation failed. `errors` is a list of {"path": ..., "message": ...}."""

    def __init__(self, errors):
        self.errors = errors
        super().__init__('; '.join(f'{e["path"]}: {e["message"]}' if e['path'] else e['message'] for e in errors))


class OperationError(Exception):
    pass


class _Classes(fields.Text):
    def clean_value(self, value, ctx, path):
        value = super().clean_value(value, ctx, path)
        if not CSS_CLASSES.match(value):
            raise fields.FieldError('Only letters, digits, spaces, "-" and "_".', path)
        return value


class _Css(fields.Text):
    def clean_value(self, value, ctx, path):
        value = super().clean_value(value, ctx, path)
        if '<' in value:
            raise fields.FieldError('CSS must not contain "<".', path)
        return value


SPACING = ['md', 'none', 'sm', 'lg', 'xl']

SECTION_STYLE = fields.Schema(
    required=False,
    # raw: no container wrapper (pages converted from the legacy tree, see pages_convert).
    width=fields.Choice(['contained', 'full', 'narrow', 'raw']),
    padding_y=fields.Choice(SPACING),
    theme=fields.Choice(['light', 'dark']),
    align=fields.Choice(['start', 'center']),
    background=fields.Schema(
        required=False,
        color=fields.Color(),
        image=fields.Image(required=False),
        overlay=fields.Number(required=False, min_value=0, max_value=90, default=0),
    ),
    # Escape hatches, mainly for pages converted from the legacy tree.
    classes=_Classes(required=False),
    css=_Css(required=False, multiline=True, max_length=20000),
)
ROW_STYLE = fields.Schema(
    required=False,
    # default: Bootstrap's own gutters (pages converted from the legacy tree).
    gap=fields.Choice(['md', 'none', 'sm', 'lg', 'default']),
    align=fields.Choice(['stretch', 'start', 'center', 'end']),
    classes=_Classes(required=False),
)
SPAN = fields.Schema(
    xs=fields.Number(min_value=1, max_value=12, default=12),
    md=fields.Number(required=False, min_value=1, max_value=12),
    lg=fields.Number(required=False, min_value=1, max_value=12),
)
WIDGET_STYLE = fields.Schema(
    required=False,
    align=fields.Choice(['inherit', 'start', 'center', 'end']),
    margin_bottom=fields.Choice(['md', 'none', 'sm', 'lg']),
    classes=_Classes(required=False),
    css=_Css(required=False, multiline=True, max_length=20000),
)


def _error(errors, path, message):
    errors.append({'path': path, 'message': message})


def _clean_with(schema, value, ctx, path, errors):
    try:
        return schema.clean(value, ctx, path)
    except fields.FieldErrors as exc:
        for err in exc.errors:
            _error(errors, err.path, err.message)
    except fields.FieldError as exc:
        _error(errors, exc.path or path, exc.message)
    return None


class _Validator:

    def __init__(self, ctx, allow_staff_widgets, assign_ids):
        self.ctx = ctx
        self.allow_staff_widgets = allow_staff_widgets
        self.assign_ids = assign_ids
        self.errors = []
        self.seen_ids = set()

    def node_id(self, node, kind, path):
        node_id = node.get('id')
        if node_id is None and self.assign_ids:
            node_id = new_id(kind)
        if not isinstance(node_id, str) or not NODE_ID.match(node_id):
            _error(self.errors, f'{path}.id', 'Missing or invalid node id.')
            return node_id
        if node_id in self.seen_ids:
            _error(self.errors, f'{path}.id', f'Duplicate node id {node_id!r}.')
        self.seen_ids.add(node_id)
        return node_id

    def expect(self, node, allowed, path):
        if not isinstance(node, dict):
            _error(self.errors, path, 'Must be an object.')
            return False
        unknown = set(node) - allowed
        if unknown:
            _error(self.errors, path, f'Unknown keys {sorted(unknown)}.')
        return True

    def document(self, doc, path=''):
        if not self.expect(doc, {'schema_version', 'sections'}, path or 'document'):
            return None
        if doc.get('schema_version', SCHEMA_VERSION) != SCHEMA_VERSION:
            _error(self.errors, f'{path}schema_version', f'Unsupported schema version {doc.get("schema_version")!r}.')
        sections = doc.get('sections', [])
        if not isinstance(sections, list):
            _error(self.errors, f'{path}sections', 'Must be a list.')
            sections = []
        return {
            'schema_version': SCHEMA_VERSION,
            'sections': [self.section(s, f'{path}sections.{i}') for i, s in enumerate(sections)],
        }

    def section(self, section, path):
        if not self.expect(section, {'id', 'pattern', 'anchor', 'style', 'rows'}, path):
            return None
        cleaned = {'id': self.node_id(section, 'section', path)}
        if section.get('pattern'):
            cleaned['pattern'] = str(section['pattern'])[:64]
        if section.get('anchor'):
            anchor = section['anchor']
            if not isinstance(anchor, str) or not fields.Link.ANCHOR.match(anchor):
                _error(self.errors, f'{path}.anchor', 'Invalid anchor.')
            cleaned['anchor'] = anchor
        cleaned['style'] = _clean_with(SECTION_STYLE, section.get('style') or {}, self.ctx, f'{path}.style', self.errors)
        rows = section.get('rows') or []
        if not isinstance(rows, list):
            _error(self.errors, f'{path}.rows', 'Must be a list.')
            rows = []
        cleaned['rows'] = [self.row(r, f'{path}.rows.{i}') for i, r in enumerate(rows)]
        return cleaned

    def row(self, row, path):
        if not self.expect(row, {'id', 'style', 'columns'}, path):
            return None
        cleaned = {'id': self.node_id(row, 'row', path)}
        cleaned['style'] = _clean_with(ROW_STYLE, row.get('style') or {}, self.ctx, f'{path}.style', self.errors)
        columns = row.get('columns') or []
        if not isinstance(columns, list) or not columns:
            _error(self.errors, f'{path}.columns', 'A row needs at least one column.')
            columns = []
        if len(columns) > 6:
            _error(self.errors, f'{path}.columns', 'At most 6 columns per row.')
        cleaned['columns'] = [self.column(c, f'{path}.columns.{i}') for i, c in enumerate(columns)]
        return cleaned

    def column(self, column, path):
        if not self.expect(column, {'id', 'span', 'valign', 'widgets'}, path):
            return None
        cleaned = {'id': self.node_id(column, 'column', path)}
        cleaned['span'] = _clean_with(SPAN, column.get('span') or {'xs': 12}, self.ctx, f'{path}.span', self.errors)
        valign = column.get('valign', 'top')
        if valign not in ('top', 'center', 'bottom'):
            _error(self.errors, f'{path}.valign', 'Must be top, center or bottom.')
        cleaned['valign'] = valign
        widgets = column.get('widgets') or []
        if not isinstance(widgets, list):
            _error(self.errors, f'{path}.widgets', 'Must be a list.')
            widgets = []
        cleaned['widgets'] = [self.widget(w, f'{path}.widgets.{i}') for i, w in enumerate(widgets)]
        return cleaned

    def widget(self, widget, path):
        if not self.expect(widget, {'id', 'type', 'props', 'style'}, path):
            return None
        cleaned = {'id': self.node_id(widget, 'widget', path), 'type': widget.get('type')}
        widget_class = get_widget(widget.get('type')) if isinstance(widget.get('type'), str) else None
        if widget_class is None:
            _error(self.errors, f'{path}.type', f'Unknown widget type {widget.get("type")!r}.')
            cleaned['props'] = widget.get('props') or {}
            return cleaned
        if widget_class.staff_only and not self.allow_staff_widgets:
            _error(self.errors, f'{path}.type', f'Widget {widget_class.key!r} is staff only.')
        props = widget.get('props')
        if props is None:
            props = widget_class.defaults()
        cleaned['props'] = _clean_with(widget_class.schema(), props, self.ctx, f'{path}.props', self.errors)
        if widget.get('style'):
            cleaned['style'] = _clean_with(WIDGET_STYLE, widget['style'], self.ctx, f'{path}.style', self.errors)
        return cleaned


def validate(doc, *, allow_keys=False, allow_staff_widgets=False, assign_ids=False, check_references=True):
    """
    Validates and cleans a page document. Returns `(cleaned_document, references)`
    where references is {"media": {...}, "page": {...}}. Raises DocumentError.

    `allow_keys`: SiteSpec mode; references may be string keys.
    `assign_ids`: give nodes without an id a fresh one (AI output, new nodes).
    `check_references`: verify that id references exist in the database.
    """
    ctx = fields.CleanContext(allow_keys=allow_keys)
    validator = _Validator(ctx, allow_staff_widgets, assign_ids)
    cleaned = validator.document(doc)
    errors = validator.errors
    if check_references and not errors:
        errors.extend(_missing_references(ctx.references))
    if errors:
        raise DocumentError(errors)
    return cleaned, ctx.references


def _missing_references(references):
    from smbs_apps.smbs_pages.models import Media, Page
    errors = []
    for kind, model in (('media', Media), ('page', Page)):
        ids = {r for r in references[kind] if isinstance(r, int)}
        missing = ids - set(model.objects.filter(id__in=ids).values_list('id', flat=True))
        for ref in sorted(missing):
            _error(errors, '', f'{kind.capitalize()} {ref} does not exist.')
    return errors


def map_references(doc, fn):
    """Returns a copy of a (valid) document with every reference replaced by fn(kind, reference)."""
    doc = copy.deepcopy(doc)
    for node, kind in walk(doc):
        if kind == 'section' and node.get('style'):
            node['style'] = SECTION_STYLE.map_references(node['style'], fn)
        elif kind == 'widget':
            widget_class = get_widget(node['type'])
            if widget_class is not None:
                node['props'] = widget_class.schema().map_references(node['props'], fn)
    return doc


def walk(doc):
    """Yields (node, kind) for every node, depth first."""
    for section in doc.get('sections', []):
        yield section, 'section'
        for row in section.get('rows', []):
            yield row, 'row'
            for column in row.get('columns', []):
                yield column, 'column'
                for widget in column.get('widgets', []):
                    yield widget, 'widget'


def find_node(doc, node_id):
    """Returns (node, kind, parent_list) or raises OperationError."""
    for section_index, section in enumerate(doc.get('sections', [])):
        if section.get('id') == node_id:
            return section, 'section', doc['sections']
        for row in section.get('rows', []):
            if row.get('id') == node_id:
                return row, 'row', section['rows']
            for column in row.get('columns', []):
                if column.get('id') == node_id:
                    return column, 'column', row['columns']
                for widget in column.get('widgets', []):
                    if widget.get('id') == node_id:
                        return widget, 'widget', column['widgets']
    raise OperationError(f'No node with id {node_id!r}.')


def reassign_ids(node, kind):
    """Gives a node and all its descendants fresh ids (for duplicates and pattern instances)."""
    node['id'] = new_id(kind)
    child_key, child_kind = {'section': ('rows', 'row'), 'row': ('columns', 'column'),
                             'column': ('widgets', 'widget')}.get(kind, (None, None))
    for child in node.get(child_key, []) if child_key else []:
        reassign_ids(child, child_kind)
    return node


# --------------------------------------------------------------------------
# Edit operations: the vocabulary shared by the visual editor and AI edits.
# --------------------------------------------------------------------------

CHILD_KIND = {'root': 'section', 'section': 'row', 'row': 'column', 'column': 'widget'}
CHILD_KEY = {'root': 'sections', 'section': 'rows', 'row': 'columns', 'column': 'widgets'}


def _container(doc, parent_id, expected_child_kind):
    if parent_id in (None, 'root'):
        parent, kind = doc, 'root'
    else:
        parent, kind, _ = find_node(doc, parent_id)
    if CHILD_KIND.get(kind) != expected_child_kind:
        raise OperationError(f'A {expected_child_kind} cannot go inside a {kind}.')
    return parent.setdefault(CHILD_KEY[kind], [])


def _insert(items, item, index):
    if index is None or index >= len(items):
        items.append(item)
    else:
        items.insert(max(0, index), item)


def apply_ops(doc, ops):
    """
    Applies edit operations to a copy of `doc` and returns it. Validate the
    result with `validate(..., assign_ids=True)` before saving.

    Operations ({"op": name, ...}):
      insert_section  {section, index?}
      insert_row      {section_id, row, index?}
      insert_widget   {column_id, widget: {type, props?}, index?}
      move_node       {node_id, parent_id, index?}       parent_id "root" for sections
      delete_node     {node_id}
      duplicate_node  {node_id}
      update_props    {node_id, props, replace?}         shallow merge unless replace
      update_style    {node_id, style}                   shallow merge
      set_columns     {row_id, spans: [{xs, md?, lg?}, ...]}
    """
    doc = copy.deepcopy(doc)
    for op in ops:
        name = op.get('op')
        handler = _OPS.get(name)
        if handler is None:
            raise OperationError(f'Unknown operation {name!r}.')
        handler(doc, op)
    return doc


def _op_insert_section(doc, op):
    section = copy.deepcopy(op['section'])
    _insert(doc.setdefault('sections', []), section, op.get('index'))


def _op_insert_row(doc, op):
    _insert(_container(doc, op['section_id'], 'row'), copy.deepcopy(op['row']), op.get('index'))


def _op_insert_widget(doc, op):
    widget = copy.deepcopy(op['widget'])
    widget_class = get_widget(widget.get('type'))
    if widget_class is None:
        raise OperationError(f'Unknown widget type {widget.get("type")!r}.')
    widget['props'] = {**widget_class.defaults(), **(widget.get('props') or {})}
    widget.setdefault('id', new_id('widget'))
    _insert(_container(doc, op['column_id'], 'widget'), widget, op.get('index'))


def _op_move_node(doc, op):
    node, kind, siblings = find_node(doc, op['node_id'])
    target = _container(doc, op.get('parent_id'), kind)
    siblings.remove(node)
    _insert(target, node, op.get('index'))


def _op_delete_node(doc, op):
    node, _, siblings = find_node(doc, op['node_id'])
    siblings.remove(node)


def _op_duplicate_node(doc, op):
    node, kind, siblings = find_node(doc, op['node_id'])
    siblings.insert(siblings.index(node) + 1, reassign_ids(copy.deepcopy(node), kind))


def _op_update_props(doc, op):
    node, kind, _ = find_node(doc, op['node_id'])
    if kind != 'widget':
        raise OperationError('update_props applies to widgets.')
    node['props'] = dict(op['props']) if op.get('replace') else {**node.get('props', {}), **op['props']}


def _op_update_style(doc, op):
    node, kind, _ = find_node(doc, op['node_id'])
    if kind == 'column':
        for key in ('span', 'valign'):
            if key in op['style']:
                node[key] = op['style'][key]
        return
    node['style'] = {**(node.get('style') or {}), **op['style']}


def _op_set_columns(doc, op):
    row, kind, _ = find_node(doc, op['row_id'])
    if kind != 'row':
        raise OperationError('set_columns applies to rows.')
    spans = op['spans']
    if not 1 <= len(spans) <= 6:
        raise OperationError('A row has 1 to 6 columns.')
    columns = row.setdefault('columns', [])
    while len(columns) > len(spans):
        removed = columns.pop()
        columns[-1].setdefault('widgets', []).extend(removed.get('widgets', []))
    while len(columns) < len(spans):
        columns.append({'id': new_id('column'), 'valign': 'top', 'widgets': []})
    for column, span in zip(columns, spans):
        column['span'] = dict(span)


_OPS = {
    'insert_section': _op_insert_section,
    'insert_row': _op_insert_row,
    'insert_widget': _op_insert_widget,
    'move_node': _op_move_node,
    'delete_node': _op_delete_node,
    'duplicate_node': _op_duplicate_node,
    'update_props': _op_update_props,
    'update_style': _op_update_style,
    'set_columns': _op_set_columns,
}


# --------------------------------------------------------------------------
# SiteSpecs
# --------------------------------------------------------------------------

SPEC_KEYS = {'schema_version', 'site', 'pages', 'chrome', 'media', 'theme'}
SPEC_PAGE_KEYS = {'key', 'name', 'slug', 'parent', 'nav_parent', 'show_on_navigation', 'navigation_order',
                  'metadata', 'document'}
SPEC_MEDIA_KEYS = {'key', 'source', 'url', 'remote_url', 'alt_text', 'caption', 'width', 'height',
                   'focal_point', 'attribution', 'name'}
MAX_DOWNLOAD_BYTES = 15 * 1024 * 1024


def validate_spec(spec):
    """Validates a SiteSpec. Returns a cleaned copy (documents cleaned, ids assigned). Raises DocumentError."""
    errors = []
    if not isinstance(spec, dict):
        raise DocumentError([{'path': '', 'message': 'A SiteSpec must be an object.'}])
    unknown = set(spec) - SPEC_KEYS
    if unknown:
        _error(errors, '', f'Unknown keys {sorted(unknown)}.')
    if spec.get('schema_version', SCHEMA_VERSION) != SCHEMA_VERSION:
        _error(errors, 'schema_version', 'Unsupported schema version.')
    cleaned = {'schema_version': SCHEMA_VERSION, 'site': dict(spec.get('site') or {}),
               'theme': spec.get('theme') or {}, 'media': [], 'pages': [], 'chrome': empty_chrome()}

    media_keys = set()
    for i, item in enumerate(spec.get('media') or []):
        path = f'media.{i}'
        if not isinstance(item, dict) or set(item) - SPEC_MEDIA_KEYS:
            _error(errors, path, f'Media items take {sorted(SPEC_MEDIA_KEYS)}.')
            continue
        key = item.get('key')
        if not isinstance(key, str) or not fields.KEY_REF.match(key) or key in media_keys:
            _error(errors, f'{path}.key', 'Missing, invalid or duplicate key.')
        media_keys.add(key)
        if not (item.get('remote_url') or item.get('url')):
            _error(errors, path, 'Needs remote_url (hotlinked) or url (downloaded).')
        if not item.get('alt_text'):
            _error(errors, f'{path}.alt_text', 'Alt text is required.')
        cleaned['media'].append(dict(item))

    page_keys, slugs = set(), set()
    pages = spec.get('pages') or []
    if not pages:
        _error(errors, 'pages', 'A SiteSpec needs at least one page.')
    for i, page in enumerate(pages):
        path = f'pages.{i}'
        if not isinstance(page, dict) or set(page) - SPEC_PAGE_KEYS:
            _error(errors, path, f'Pages take {sorted(SPEC_PAGE_KEYS)}.')
            continue
        key, slug = page.get('key'), page.get('slug')
        if not isinstance(key, str) or not fields.KEY_REF.match(key) or key in page_keys:
            _error(errors, f'{path}.key', 'Missing, invalid or duplicate key.')
        page_keys.add(key)
        if slug in slugs:
            _error(errors, f'{path}.slug', f'Duplicate slug {slug!r}.')
        slugs.add(slug)
        if not page.get('name'):
            _error(errors, f'{path}.name', 'Required.')
        cleaned['pages'].append(dict(page))
    if None not in slugs and pages:
        _error(errors, 'pages', 'One page must be the home page (slug null).')

    def check_refs(refs, path):
        for kind, known in (('media', media_keys), ('page', page_keys)):
            for ref in refs[kind]:
                if isinstance(ref, str) and ref not in known:
                    _error(errors, path, f'Unknown {kind} key {ref!r}.')

    for page in cleaned['pages']:
        for ref_name in ('parent', 'nav_parent'):
            if page.get(ref_name) is not None and page[ref_name] not in page_keys:
                _error(errors, f'pages.{page.get("key")}.{ref_name}', f'Unknown page key {page[ref_name]!r}.')
        try:
            page['document'], refs = validate(page.get('document') or empty_document(), allow_keys=True,
                                              assign_ids=True, check_references=False)
            check_refs(refs, f'pages.{page.get("key")}.document')
        except DocumentError as exc:
            errors.extend({'path': f'pages.{page.get("key")}.document.{e["path"]}', 'message': e['message']}
                          for e in exc.errors)
    chrome = spec.get('chrome') or {}
    for part in ('header', 'footer'):
        try:
            cleaned['chrome'][part], refs = validate(chrome.get(part) or empty_document(), allow_keys=True,
                                                     assign_ids=True, check_references=False)
            check_refs(refs, f'chrome.{part}')
        except DocumentError as exc:
            errors.extend({'path': f'chrome.{part}.{e["path"]}', 'message': e['message']} for e in exc.errors)
    if errors:
        raise DocumentError(errors)
    return cleaned


def _download(url):
    import requests
    with requests.get(url, stream=True, timeout=30) as response:
        response.raise_for_status()
        chunks, size = [], 0
        for chunk in response.iter_content(64 * 1024):
            size += len(chunk)
            if size > MAX_DOWNLOAD_BYTES:
                raise DocumentError([{'path': '', 'message': f'{url} is larger than {MAX_DOWNLOAD_BYTES} bytes.'}])
            chunks.append(chunk)
    return b''.join(chunks)


def materialize(spec, *, user=None, publish=True, theme_handler=None):
    """
    Applies a SiteSpec to this site in one transaction: creates media, creates
    or updates pages (matched by slug) as document pages, sets the header and
    footer, and (by default) publishes everything. `theme_handler(theme)` is
    called with the spec's theme tokens if given (themes live in the host).

    Returns {"pages": {key: id}, "media": {key: id}}.
    """
    from django.contrib.sites.models import Site
    from django.core.files.base import ContentFile
    from smbs_apps.smbs_base.models import ObjectMetadata
    from smbs_apps.smbs_pages import services
    from smbs_apps.smbs_pages.models import Media, Page, SiteChrome

    spec = validate_spec(spec)
    site = Site.objects.get_current()
    # Downloads happen before the transaction so a slow URL doesn't hold it open.
    downloads = {item['key']: _download(item['url']) for item in spec['media']
                 if item.get('url') and not item.get('remote_url')}

    with transaction.atomic():
        if spec['site'].get('name'):
            site.name = spec['site']['name'][:50]
            site.save(update_fields=['name'])

        media_ids = {}
        for item in spec['media']:
            media = None
            if item.get('remote_url'):
                media = Media.objects.filter(remote_url=item['remote_url']).first()
            media = media or Media()
            media.name = item.get('name') or item['key']
            media.media_type = Media.IMAGE
            media.source = item.get('source') or (Media.UNSPLASH if item.get('remote_url') else Media.UPLOAD)
            media.remote_url = item.get('remote_url') or ''
            media.alt_text = item['alt_text'][:250]
            media.caption = (item.get('caption') or '')[:500]
            media.width, media.height = item.get('width'), item.get('height')
            media.focal_point = item.get('focal_point')
            media.attribution = item.get('attribution') or {}
            if item['key'] in downloads:
                filename = item['url'].split('?')[0].rsplit('/', 1)[-1] or f'{item["key"]}.jpg'
                media.file.save(filename, ContentFile(downloads[item['key']]), save=False)
            media.save()
            media_ids[item['key']] = media.id

        pages_by_key = {}
        for item in spec['pages']:
            page = Page.objects.filter(site=site, slug=item.get('slug')).first()
            if page is None:
                # New pages are document pages; existing legacy pages switch when published.
                page = Page(site=site, slug=item.get('slug'), content_mode=Page.ContentMode.DOCUMENT)
            page.name = item['name']
            page.active = True
            page.show_on_navigation = item.get('show_on_navigation', True)
            page.navigation_order = item.get('navigation_order')
            page.parent = None
            page.save()
            pages_by_key[item['key']] = page
        for item in spec['pages']:
            page = pages_by_key[item['key']]
            page.parent = pages_by_key.get(item.get('parent'))
            page.nav_parent = pages_by_key.get(item.get('nav_parent'))
            metadata = item.get('metadata') or {}
            if metadata:
                page.metadata = page.metadata or ObjectMetadata()
                page.metadata.title = (metadata.get('title') or page.name)[:300]
                page.metadata.description = (metadata.get('description') or '')[:300]
                page.metadata.save()
            page.save()

        def resolve(kind, ref):
            if isinstance(ref, int):
                return ref
            return media_ids[ref] if kind == 'media' else pages_by_key[ref].id

        for item in spec['pages']:
            page = pages_by_key[item['key']]
            document = map_references(item['document'], resolve)
            services.save_draft(page, document, user=user)
            if publish:
                services.publish_page(page, user=user, note='Generated site')

        chrome = SiteChrome.get_object() or SiteChrome(site=site)
        chrome.draft = {part: map_references(spec['chrome'][part], resolve) for part in ('header', 'footer')}
        chrome.draft_version += 1
        chrome.save()
        if publish:
            services.publish_chrome(chrome)

        if theme_handler and spec['theme']:
            theme_handler(spec['theme'])

    return {'pages': {key: page.id for key, page in pages_by_key.items()}, 'media': media_ids}


def export():
    """Reads this site's document pages, chrome and media back as a SiteSpec (references become keys)."""
    from django.contrib.sites.models import Site
    from smbs_apps.smbs_pages.models import Media, Page, SiteChrome

    site = Site.objects.get_current()
    pages = list(Page.objects.filter(site=site, content_mode=Page.ContentMode.DOCUMENT).order_by('id'))
    media_ids = set()

    def to_key(kind, ref):
        if kind == 'media':
            media_ids.add(ref)
            return f'media-{ref}'
        return f'page-{ref}'

    spec_pages = []
    for page in pages:
        spec_pages.append({
            'key': f'page-{page.id}',
            'name': page.name,
            'slug': page.slug,
            'parent': f'page-{page.parent_id}' if page.parent_id else None,
            'nav_parent': f'page-{page.nav_parent_id}' if page.nav_parent_id else None,
            'show_on_navigation': page.show_on_navigation,
            'navigation_order': page.navigation_order,
            'metadata': {'title': page.metadata.title or '', 'description': page.metadata.description or ''}
            if page.metadata_id else {},
            'document': map_references(page.draft, to_key),
        })
    chrome = SiteChrome.get_object()
    chrome_draft = chrome.draft if chrome else empty_chrome()
    spec_chrome = {part: map_references(chrome_draft.get(part) or empty_document(), to_key)
                   for part in ('header', 'footer')}
    spec_media = []
    for media in Media.objects.filter(id__in=media_ids).order_by('id'):
        item = {'key': f'media-{media.id}', 'name': media.name or '', 'source': media.source,
                'alt_text': media.alt_text or media.name or 'Image', 'attribution': media.attribution}
        if media.remote_url:
            item['remote_url'] = media.remote_url
        else:
            item['url'] = media.file_url
        spec_media.append(item)
    return {'schema_version': SCHEMA_VERSION, 'site': {'name': site.name}, 'theme': {},
            'pages': spec_pages, 'chrome': spec_chrome, 'media': spec_media}
