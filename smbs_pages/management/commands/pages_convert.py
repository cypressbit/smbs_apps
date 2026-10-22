"""
Converts legacy (Container/Row/Column/Widget) pages into page documents.

The converted document is saved as the page's draft; visitors keep seeing the
legacy tree until it is published (`--publish`, or later from the editor).
Preview a converted draft with the URL printed for each page.

    manage.py pages_convert --page 12            # one page, draft only
    manage.py pages_convert --all --dry-run      # report what would change
    manage.py pages_convert --page 12 --publish  # convert and go live
"""
from django.core.management.base import BaseCommand, CommandError

from smbs_apps.smbs_pages import documents, services
from smbs_apps.smbs_pages.models import Page
from smbs_apps.smbs_pages.widgets import get_widget


def _style(classes, css, extra=None):
    style = dict(extra or {})
    if classes:
        style['classes'] = classes
    if css:
        style['css'] = css
    return style


def convert_page(page):
    """Builds a page document from a legacy page tree. Returns (document, warnings)."""
    warnings = []
    sections = []
    for container, content in page.get_content_tree()['containers'].items():
        # The legacy template used custom_classes *instead of* "container", so a
        # container with custom classes becomes a "raw" section carrying them.
        classes = (container.custom_classes or '').strip()
        width = 'raw' if classes else 'contained'
        rows = []
        for row, row_content in content['rows'].items():
            columns = []
            for column, widgets in row_content['columns'].items():
                nodes = []
                for widget in widgets:
                    if get_widget(widget.type) is None:
                        warnings.append(f'Widget {widget.id} has unknown type {widget.type!r}; skipped.')
                        continue
                    node = {
                        'id': documents.new_id('widget'),
                        'type': widget.type,
                        'props': {
                            'content': widget.content or '',
                            'classes': widget.custom_classes or '',
                            'options': widget.options or {},
                            'media': list(widget.media.values_list('id', flat=True)),
                        },
                    }
                    style = _style('', widget.custom_css, {'margin_bottom': 'none'})
                    node['style'] = style
                    nodes.append(node)
                columns.append({
                    'id': documents.new_id('column'),
                    # Legacy columns rendered as col-md-<width> (full width on phones).
                    'span': {'xs': 12, 'md': column.width},
                    'valign': 'top',
                    'widgets': nodes,
                })
            if columns:
                rows.append({'id': documents.new_id('row'),
                             'style': _style(row.custom_classes or '', '', {'gap': 'default'}),
                             'columns': columns})
        sections.append({
            'id': documents.new_id('section'),
            'style': _style(classes, container.custom_css, {'width': width, 'padding_y': 'none'}),
            'rows': rows,
        })
    return {'schema_version': documents.SCHEMA_VERSION, 'sections': sections}, warnings


class Command(BaseCommand):
    help = 'Convert legacy page trees into page documents (saved as drafts).'

    def add_arguments(self, parser):
        target = parser.add_mutually_exclusive_group(required=True)
        target.add_argument('--page', type=int, action='append', help='Page id (repeatable).')
        target.add_argument('--all', action='store_true', help='Every legacy page on this site.')
        parser.add_argument('--publish', action='store_true', help='Publish after converting.')
        parser.add_argument('--dry-run', action='store_true', help='Only report.')

    def handle(self, *args, **options):
        pages = Page.objects.filter(content_mode=Page.ContentMode.LEGACY, external_url__isnull=True)
        if options['page']:
            pages = pages.filter(pk__in=options['page'])
            if pages.count() != len(set(options['page'])):
                raise CommandError('Some pages do not exist or are already document pages.')
        for page in pages.order_by('id'):
            document, warnings = convert_page(page)
            widget_count = sum(1 for _, kind in documents.walk(document) if kind == 'widget')
            for warning in warnings:
                self.stderr.write(f'  page {page.id}: {warning}')
            if options['dry_run']:
                self.stdout.write(f'page {page.id} "{page}": {len(document["sections"])} sections, {widget_count} widgets')
                continue
            services.save_draft(page, document, allow_staff_widgets=True)
            line = f'page {page.id} "{page}": converted ({widget_count} widgets)'
            if options['publish']:
                services.publish_page(page, note='Converted from legacy widget tree')
                line += ', published'
            else:
                line += f'; preview: {page.get_absolute_url()}?preview={services.preview_token(page)}'
            self.stdout.write(self.style.SUCCESS(line))
