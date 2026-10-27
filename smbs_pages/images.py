"""
Responsive images: smaller copies of uploaded images, and the srcset that lets
the browser pick one.

Uploads get WebP copies at WIDTHS (never wider than the original), made once
when the file is saved and listed in Media.variants:
    {"source": "page/media/x.jpg", "widths": {"480": "page/media/variants/x-480.webp", ...}}
Unsplash photos are hotlinked, so their sizes come from URL parameters instead.
Anything else (SVG, animated GIF, a file Pillow can't read) is served as it is.
"""
import io
import logging
from pathlib import PurePosixPath
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.core.files.base import ContentFile


logger = logging.getLogger(__name__)

WIDTHS = (480, 960, 1440, 2000)
QUALITY = 80


def build_variants(media):
    """Makes the WebP copies for an uploaded image. Returns Media.variants; {} when there's nothing to make."""
    from PIL import Image, ImageOps

    storage = media.file.storage
    with media.file.open('rb') as handle, Image.open(handle) as image:
        if getattr(image, 'is_animated', False):
            return {}
        image = ImageOps.exif_transpose(image)  # phone photos: keep them the right way up
        image.load()
    if image.mode not in ('RGB', 'RGBA'):
        image = image.convert('RGBA' if 'A' in image.getbands() or 'transparency' in image.info else 'RGB')
    media.width, media.height = image.size  # as shown, after rotating
    stem = PurePosixPath(media.file.name).stem
    widths = {}
    # Largest first, so each copy is resized from a smaller one.
    for width in sorted({w for w in WIDTHS if w < image.width} | {min(image.width, WIDTHS[-1])}, reverse=True):
        if width < image.width:
            image = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, 'WEBP', quality=QUALITY, method=4)
        widths[str(width)] = storage.save(f'page/media/variants/{stem}-{width}.webp', ContentFile(buffer.getvalue()))
    return {'source': media.file.name, 'widths': widths}


def update_variants(media):
    """Rebuilds the copies when the file changed. Never fails the save: the original still works."""
    if not media.file or media.variants.get('source') == media.file.name:
        return
    old = (media.variants or {}).get('widths', {}).values()
    try:
        variants = build_variants(media)
    except Exception:
        logger.exception('Could not make smaller copies of %s', media.file.name)
        variants = {}
    variants = variants or {'source': media.file.name, 'widths': {}}
    for name in set(old) - set(variants['widths'].values()):
        try:
            media.file.storage.delete(name)
        except Exception:
            logger.warning('Could not delete %s', name)
    media.variants = variants
    type(media).objects.filter(pk=media.pk).update(variants=variants, width=media.width, height=media.height)


def candidates(media):
    """[(url, width)] smallest first, or [] when the image has a single size."""
    if not media:
        return []
    if media.remote_url.startswith('https://images.unsplash.com/'):
        widths = [w for w in WIDTHS if not media.width or w <= media.width]
        return [(_unsplash(media.remote_url, w), w) for w in widths]
    widths = (media.variants or {}).get('widths') or {}
    storage = media.file.storage
    return sorted(((storage.url(name), int(width)) for width, name in widths.items()), key=lambda c: c[1])


def src(media, width=1440):
    """The URL of the copy closest to `width` (rounding up), or the original."""
    sizes = candidates(media)
    if not sizes:
        return media.url if media else ''
    return next((url for url, w in sizes if w >= width), sizes[-1][0])


def srcset(media):
    return ', '.join(f'{url} {width}w' for url, width in candidates(media))


def _unsplash(url, width):
    """Unsplash (imgix) resizes on request: https://unsplash.com/documentation#dynamically-resizable-images"""
    parts = urlsplit(url)
    query = {k: v for k, v in parse_qsl(parts.query) if k not in ('w', 'h', 'q', 'auto')}
    query.update({'w': str(width), 'q': '75', 'auto': 'format'})
    return urlunsplit(parts._replace(query=urlencode(query)))
