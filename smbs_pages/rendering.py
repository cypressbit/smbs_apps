"""
Renders page documents to HTML (Bootstrap 5 grid plus the token classes in
static/smbs_pages/sections.css).

In edit mode every node carries `data-db-node` / `data-db-kind` attributes so
the visual editor can select it, and a widget that fails to render shows a
placeholder instead of disappearing.

Sections from a pattern that needs a capability (e.g. the shop's), and widgets
that need one, render nothing while the site hasn't enabled it
(settings.SITE_CAPABILITIES; a host without that setting has every capability);
the editor shows them with a note instead. So a page can carry its shop
sections before the owner turns the shop on.
"""
import logging

from django.conf import settings
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe

from smbs_apps.smbs_pages.widgets import get_widget


logger = logging.getLogger(__name__)

GAP = {'none': 'g-0', 'sm': 'g-2', 'md': 'g-4', 'lg': 'g-5', 'default': ''}
ROW_ALIGN = {'stretch': '', 'start': 'align-items-start', 'center': 'align-items-center', 'end': 'align-items-end'}
VALIGN = {'top': '', 'center': 'align-self-center', 'bottom': 'align-self-end'}
WIDGET_ALIGN = {'inherit': '', 'start': 'text-start', 'center': 'text-center', 'end': 'text-end'}
CAPABILITY_NAMES = {'shop': 'the shop', 'blog': 'the blog'}


def _capability_off(capability):
    enabled = getattr(settings, 'SITE_CAPABILITIES', None)
    return bool(capability) and enabled is not None and capability not in enabled


def _section_capability(section):
    from smbs_apps.smbs_pages import patterns
    if not section.get('pattern'):
        return None
    try:
        return patterns.get_pattern(section['pattern']).get('capability')
    except patterns.UnknownPattern:
        return None


def _off_note(capability):
    return format_html('<div class="db-capability-off">Visitors see this once {} is turned on.</div>',
                       CAPABILITY_NAMES.get(capability, capability))
CONTAINER = {'contained': 'container', 'full': 'container-fluid px-0', 'narrow': 'container db-narrow', 'raw': ''}


def _classes(*names):
    return ' '.join(name for name in names if name)


def _edit_attrs(edit, node, kind):
    if not edit:
        return ''
    return format_html(' data-db-node="{}" data-db-kind="{}"', node['id'], kind)


def _background_css(media_id):
    from smbs_apps.smbs_pages.models import Media
    from smbs_apps.smbs_pages.templatetags.smbs_documents import background_css
    return background_css(Media.objects.filter(pk=media_id).first())


class Renderer:

    def __init__(self, context=None, edit=False):
        # Widgets see `editing` to mark their fields for in-place editing ({% db_field %}).
        self.context = {**(context or {}), 'editing': edit}
        self.edit = edit
        self._section_off = False

    def document(self, doc):
        return mark_safe(''.join(self.section(section) for section in doc.get('sections', [])))

    def section(self, section):
        capability = _section_capability(section)
        off = _capability_off(capability)
        if off and not self.edit:
            return ''
        style = section.get('style') or {}
        background = style.get('background') or {}
        color = background.get('color') or ''
        classes = _classes(
            'db-section',
            f'db-pad-{style.get("padding_y", "md")}',
            f'db-theme-{style.get("theme", "light")}',
            f'db-bg-{color}' if color and not color.startswith('#') else '',
            'text-center' if style.get('align') == 'center' else '',
            'db-has-bg-image db-bg-responsive' if background.get('image') else '',
            style.get('classes', '') if style.get('width') != 'raw' else '',
            'db-section-off' if off else '',
        )
        css = []
        if color.startswith('#'):
            css.append(f'background-color:{color}')
        image = background.get('image')
        if image:
            background_image = _background_css(image['media'])
            if background_image:
                css.append(background_image)
                focal = image.get('focal_point')
                if focal:
                    css.append(f'background-position:{focal["x"] * 100:.0f}% {focal["y"] * 100:.0f}%')
        if background.get('overlay'):
            css.append(f'--db-overlay:{background["overlay"] / 100:.2f}')
        narrow = style.get('width') == 'narrow'
        self._section_off = off
        rows = ''.join(self.row(row, narrow=narrow) for row in section.get('rows', []))
        self._section_off = False
        if off:
            rows = _off_note(capability) + rows
        custom_css = format_html('<style>{}</style>', mark_safe(style['css'])) if style.get('css') else ''
        return format_html(
            '{}<section class="{}"{}{}{}><div class="{}">{}</div></section>',
            custom_css,
            classes,
            format_html(' id="{}"', section['anchor']) if section.get('anchor') else '',
            format_html(' style="{}"', mark_safe(';'.join(conditional_escape(part) for part in css))) if css else '',
            _edit_attrs(self.edit, section, 'section'),
            style.get('classes', '') if style.get('width') == 'raw' else CONTAINER.get(style.get('width', 'contained'), 'container'),
            mark_safe(rows),
        )

    def row(self, row, narrow=False):
        style = row.get('style') or {}
        columns = row.get('columns', [])
        # A single column narrower than its row used to sit against the left edge (an FAQ under its
        # heading looked off-center). In a narrow section, which already limits the width, it fills the
        # row, lining up with the section's other rows; elsewhere it sits in the middle.
        lone = len(columns) == 1 and any(n and int(n) < 12 for n in (columns[0].get('span') or {}).values())
        classes = _classes('row', GAP.get(style.get('gap', 'md'), ''), ROW_ALIGN.get(style.get('align', 'stretch'), ''),
                           'justify-content-center' if lone and not narrow else '', style.get('classes', ''))
        columns = ''.join(self.column(column, full=lone and narrow) for column in columns)
        return format_html('<div class="{}"{}>{}</div>', classes, _edit_attrs(self.edit, row, 'row'), mark_safe(columns))

    def column(self, column, full=False):
        span = {'xs': 12} if full else (column.get('span') or {'xs': 12})
        classes = _classes(
            f'col-{span.get("xs", 12)}',
            f'col-md-{span["md"]}' if span.get('md') else '',
            f'col-lg-{span["lg"]}' if span.get('lg') else '',
            VALIGN.get(column.get('valign', 'top'), ''),
            'db-column',
        )
        widgets = ''.join(self.widget(widget) for widget in column.get('widgets', []))
        return format_html('<div class="{}"{}>{}</div>', classes, _edit_attrs(self.edit, column, 'column'),
                           mark_safe(widgets))

    def widget(self, widget):
        widget_class = get_widget(widget.get('type'))
        style = widget.get('style') or {}
        try:
            if widget_class is None:
                raise LookupError(f'Unknown widget type {widget.get("type")!r}')
            if _capability_off(widget_class.capability):
                if not self.edit:
                    return ''
                # Its pages (e.g. the cart) don't exist yet, so it can't render: show what it is.
                html = format_html('<div class="db-capability-off"><i class="bi bi-{} me-1" aria-hidden="true"></i>{}</div>',
                                   widget_class.icon, widget_class.NAME) if self._section_off else \
                    format_html('{}{}', widget_class.NAME, _off_note(widget_class.capability))
            else:
                html = widget_class(widget.get('props') or {}, self.context, node=widget).render()
        except Exception:
            logger.exception('Widget %s (%s) failed to render', widget.get('id'), widget.get('type'))
            if not self.edit:
                return ''
            html = format_html('<div class="db-widget-error">{} could not be displayed.</div>',
                               widget_class.NAME if widget_class else widget.get('type'))
        classes = _classes(
            'db-widget',
            f'db-widget-{widget.get("type", "").replace("_", "-").replace(".", "-")}',
            WIDGET_ALIGN.get(style.get('align', 'inherit'), ''),
            f'db-mb-{style.get("margin_bottom", "md")}',
            style.get('classes', ''),
        )
        custom_css = format_html('<style>{}</style>', mark_safe(style['css'])) if style.get('css') else ''
        return format_html('{}<div class="{}"{}>{}</div>', custom_css, classes,
                           _edit_attrs(self.edit, widget, 'widget'), mark_safe(html))


def render_document(doc, context=None, *, edit=False):
    return Renderer(context, edit).document(doc or {})


def render_section(doc, section_id, context=None, *, edit=False):
    """Renders one section; the editor re-renders only what changed."""
    for section in (doc or {}).get('sections', []):
        if section.get('id') == section_id:
            return Renderer(context, edit).section(section)
    return mark_safe('')

