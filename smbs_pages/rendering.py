"""
Renders page documents to HTML (Bootstrap 5 grid plus the token classes in
static/smbs_pages/sections.css).

In edit mode every node carries `data-db-node` / `data-db-kind` attributes so
the visual editor can select it, and a widget that fails to render shows a
placeholder instead of disappearing.
"""
import logging

from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

from smbs_apps.smbs_pages.widgets import get_widget


logger = logging.getLogger(__name__)

GAP = {'none': 'g-0', 'sm': 'g-2', 'md': 'g-4', 'lg': 'g-5', 'default': ''}
ROW_ALIGN = {'stretch': '', 'start': 'align-items-start', 'center': 'align-items-center', 'end': 'align-items-end'}
VALIGN = {'top': '', 'center': 'align-self-center', 'bottom': 'align-self-end'}
WIDGET_ALIGN = {'inherit': '', 'start': 'text-start', 'center': 'text-center', 'end': 'text-end'}
CONTAINER = {'contained': 'container', 'full': 'container-fluid px-0', 'narrow': 'container db-narrow', 'raw': ''}


def _classes(*names):
    return ' '.join(name for name in names if name)


def _edit_attrs(edit, node, kind):
    if not edit:
        return ''
    return format_html(' data-db-node="{}" data-db-kind="{}"', node['id'], kind)


def _media_url(media_id):
    from smbs_apps.smbs_pages.models import Media
    media = Media.objects.filter(pk=media_id).first()
    return media.url if media else ''


class Renderer:

    def __init__(self, context=None, edit=False):
        self.context = context if context is not None else {}
        self.edit = edit

    def document(self, doc):
        return mark_safe(''.join(self.section(section) for section in doc.get('sections', [])))

    def section(self, section):
        style = section.get('style') or {}
        background = style.get('background') or {}
        color = background.get('color') or ''
        classes = _classes(
            'db-section',
            f'db-pad-{style.get("padding_y", "md")}',
            f'db-theme-{style.get("theme", "light")}',
            f'db-bg-{color}' if color and not color.startswith('#') else '',
            'text-center' if style.get('align') == 'center' else '',
            'db-has-bg-image' if background.get('image') else '',
            style.get('classes', '') if style.get('width') != 'raw' else '',
        )
        css = []
        if color.startswith('#'):
            css.append(f'background-color:{color}')
        image = background.get('image')
        if image:
            url = _media_url(image['media'])
            if url:
                css.append(f"background-image:url('{escape(url)}')")
                focal = image.get('focal_point')
                if focal:
                    css.append(f'background-position:{focal["x"] * 100:.0f}% {focal["y"] * 100:.0f}%')
        if background.get('overlay'):
            css.append(f'--db-overlay:{background["overlay"] / 100:.2f}')
        rows = ''.join(self.row(row) for row in section.get('rows', []))
        custom_css = format_html('<style>{}</style>', mark_safe(style['css'])) if style.get('css') else ''
        return format_html(
            '{}<section class="{}"{}{}{}><div class="{}">{}</div></section>',
            custom_css,
            classes,
            format_html(' id="{}"', section['anchor']) if section.get('anchor') else '',
            format_html(' style="{}"', ';'.join(css)) if css else '',
            _edit_attrs(self.edit, section, 'section'),
            style.get('classes', '') if style.get('width') == 'raw' else CONTAINER.get(style.get('width', 'contained'), 'container'),
            mark_safe(rows),
        )

    def row(self, row):
        style = row.get('style') or {}
        classes = _classes('row', GAP.get(style.get('gap', 'md'), ''), ROW_ALIGN.get(style.get('align', 'stretch'), ''),
                           style.get('classes', ''))
        columns = ''.join(self.column(column) for column in row.get('columns', []))
        return format_html('<div class="{}"{}>{}</div>', classes, _edit_attrs(self.edit, row, 'row'), mark_safe(columns))

    def column(self, column):
        span = column.get('span') or {'xs': 12}
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

