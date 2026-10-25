"""Template helpers for document widgets: links, media attribution and editor field markers."""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.http import urlencode

from smbs_apps.smbs_pages.models import Media, Page


register = template.Library()


@register.filter
def link_href(link):
    """The href for a Link field value ({"kind": "page" | "url" | "email" | "tel" | "anchor", ...})."""
    if not link:
        return '#'
    kind = link.get('kind')
    if kind == 'page':
        page = Page.objects.filter(pk=link['page']).first()
        return page.get_absolute_url() if page else '#'
    if kind == 'url':
        return link['url']
    if kind == 'email':
        return f'mailto:{link["email"]}'
    if kind == 'tel':
        return 'tel:' + ''.join(c for c in link['tel'] if c.isdigit() or c == '+')
    if kind == 'anchor':
        return f'#{link["anchor"]}'
    return '#'


@register.filter
def link_target(link):
    if link and link.get('new_tab'):
        return mark_safe(' target="_blank" rel="noopener"')
    return ''


@register.simple_tag
def media_attribution(media):
    """The credit line stock providers require, e.g. "Photo by Jane Doe on Unsplash"."""
    if not isinstance(media, Media) or media.source != Media.UNSPLASH or not media.attribution.get('name'):
        return ''
    utm = urlencode({'utm_source': media.attribution.get('app_name', 'digitally_boosted'), 'utm_medium': 'referral'})
    profile = media.attribution.get('profile_url', 'https://unsplash.com')
    return format_html(
        '<small class="db-attribution d-block mt-1 opacity-75">Photo by <a href="{}?{}" rel="noopener">{}</a> on '
        '<a href="https://unsplash.com/?{}" rel="noopener">Unsplash</a></small>',
        profile, utm, media.attribution['name'], utm)


@register.simple_tag
def media_for(image):
    """The Media for an Image field value, or None: {% media_for props.image as media %}."""
    if not image or not image.get('media'):
        return None
    return Media.objects.filter(pk=image['media']).first()


@register.filter
def focal_position(image):
    """CSS object-position for an Image field value with a focal point."""
    focal = (image or {}).get('focal_point')
    if not focal:
        return ''
    return f'{focal["x"] * 100:.0f}% {focal["y"] * 100:.0f}%'


@register.filter
def dom_id(node, suffix=''):
    """A DOM id unique to a document node, e.g. for accordions and carousels."""
    node_id = (node or {}).get('id') or 'db-node'
    return f'{node_id}-{suffix}' if suffix else node_id


@register.simple_tag(takes_context=True)
def db_field(context, *path, rich=False):
    """
    In the visual editor, marks an element as the text of a widget field so it
    can be edited in place: {% db_field 'heading' %} or, inside a repeater,
    {% db_field 'items' forloop.counter0 'title' %}. Outputs nothing on the
    published site.
    """
    if not context.get('editing'):
        return ''
    return format_html(' data-db-field="{}"{}', '.'.join(str(part) for part in path),
                       mark_safe(' data-db-rich') if rich else '')
