"""
Structured data (schema.org JSON-LD) for a document site's home page: who the
business is, built only from what the owner published (the site's name, the
map's address, phone and email links, the logo and the page description).
Nothing is guessed: a site without an address or phone is an Organization,
not a LocalBusiness, and opening hours (free text) are left out.
"""
import json

from smbs_apps.smbs_pages import documents
from smbs_apps.smbs_pages.models import Media


def _links(document, kind):
    for node, node_kind in documents.walk(document or {}):
        if node_kind != 'widget':
            continue
        for value in _walk_values(node.get('props') or {}):
            if isinstance(value, dict) and value.get('kind') == kind and value.get(kind):
                yield value[kind]


def _walk_values(value):
    yield value
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_values(item)


def _first_widget(documents_, widget_type):
    for document in documents_:
        for node, kind in documents.walk(document or {}):
            if kind == 'widget' and node.get('type') == widget_type:
                return node.get('props') or {}
    return None


def local_business(*, name, url, description, page_document, chrome_document, media_url=None):
    """The JSON-LD object for the business, or None if there's nothing to say beyond its name."""
    sources = [page_document, (chrome_document or {}).get('header'), (chrome_document or {}).get('footer')]
    data = {'@context': 'https://schema.org', 'name': name, 'url': url}
    if description:
        data['description'] = description
    map_props = _first_widget(sources, 'location_map')
    if map_props and map_props.get('address'):
        data['address'] = map_props['address']
    phone = next((tel for source in sources for tel in _links(source, 'tel')), None)
    if phone:
        data['telephone'] = phone
    email = next((mail for source in sources for mail in _links(source, 'email')), None)
    if email:
        data['email'] = email
    logo = _first_widget(sources, 'site_logo')
    if logo and logo.get('logo') and media_url:
        media = Media.objects.filter(pk=(logo['logo'] or {}).get('media')).first()
        if media and media.file:
            data['logo'] = data['image'] = media_url(media.file.url)
    data['@type'] = 'LocalBusiness' if ('address' in data or 'telephone' in data) else 'Organization'
    if set(data) <= {'@context', '@type', 'name', 'url'}:
        return None
    return data


def as_script(data):
    text = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    return f'<script type="application/ld+json">{text}</script>'
