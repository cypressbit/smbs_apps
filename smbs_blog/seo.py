import re

from bs4 import BeautifulSoup

from django.utils.translation import gettext as _
from django.contrib.sites.models import Site


CHAR_REGEX = '[-()\"#/@;:<>{}`+=~|.!¡?¿,“”]'
CHAR_SUB = ' '


def sub(string):
    return re.sub(CHAR_REGEX, CHAR_SUB, string.lower())


def post_word_count(post, min_count):
    soup = BeautifulSoup(post.content, 'html.parser')
    for script in soup(['script', 'style']):
        script.decompose()

    text = soup.get_text().split()
    success = len(text) >= min_count

    if success:
        message = _('Content meets the minimum word count')
    else:
        message = _('Content does not meet the minimum word count')

    results = {
        'results': len(text),
        'success': success,
        'message': message,
    }
    return results


def post_tags(post, min_count):
    if post.pk:
        tag_count = post.tags.count()
        success = tag_count >= min_count

        if success:
            message = _('Post meets the minimum tag count')
        else:
            message = _('Post does not meet the minimum tag count')
    else:
        tag_count = 'N/A'
        success = False
        message = _('Post needs to be saved first to run the tag check')

    results = {
        'results': tag_count,
        'success': success,
        'message': message,
    }
    return results


def post_images(post, min_count):
    soup = BeautifulSoup(post.content, 'html.parser')
    for script in soup(['script', 'style']):
        script.decompose()

    images = soup.findAll('img')
    total_images = len(images)
    if post.cover_image:
        total_images += 1
    success = total_images >= min_count

    if success:
        message = _('Content meets the minimum image count')
    else:
        message = _('Content does not meet the minimum image count')

    results = {
        'results': len(images),
        'success': success,
        'message': message,
    }
    return results


def post_internal_links(post, min_count):
    soup = BeautifulSoup(post.content, 'html.parser')
    for script in soup(['script', 'style']):
        script.decompose()

    links = soup.findAll('a')
    site = Site.objects.get_current()
    internal_links = []

    for link in links:
        href = link.get('href')
        if href.startswith('/') or site.domain in href:
            internal_links.append(href)

    success = len(internal_links) >= min_count

    if success:
        message = _('Content meets the minimum internal link count')
    else:
        message = _('Content does not meet the minimum internal link count')

    results = {
        'results': len(internal_links),
        'success': success,
        'message': message,
    }
    return results


def post_external_links(post, min_count):
    soup = BeautifulSoup(post.content, 'html.parser')
    for script in soup(['script', 'style']):
        script.decompose()

    links = soup.findAll('a')
    site = Site.objects.get_current()
    external_links = []

    for link in links:
        href = link.get('href')
        if not href.startswith('/') and site.domain not in href:
            external_links.append(href)

    success = len(external_links) >= min_count

    if success:
        message = _('Content meets the minimum external link count')
    else:
        message = _('Content does not meet the minimum external link count')

    results = {
        'results': len(external_links),
        'success': success,
        'message': message,
    }
    return results


def post_keywords(post, min_count):
    soup = BeautifulSoup(post.content, 'html.parser')

    for script in soup(['script', 'style']):
        script.decompose()

    content_words = set(sub(soup.get_text()).split())
    title_words = set(sub(post.title).split())
    description_words = set(sub(post.description).split())
    keywords = content_words & title_words & description_words
    keywords = [i for i in keywords if len(i) > 2]
    success = len(keywords) >= min_count

    if success:
        message = _('Post meets the minimum keyword count')
    else:
        message = _('Post does not meet the minimum keyword count')

    results = {
        'results': ', '.join(keywords),
        'success': success,
        'message': message,
    }
    return results


CHECK_MAP = {
    'word_count': post_word_count,
    'tags': post_tags,
    'images': post_images,
    'internal_links': post_internal_links,
    'external_links': post_external_links,
    'keywords': post_keywords,
}


def run_seo_checks(seo_checks, settings, post_instance):
    results = {}
    errors = []

    for check in seo_checks:
        check_function = CHECK_MAP.get(check)
        check_settings = settings.get(check)
        results[check] = check_function(post_instance, **check_settings)

        if not results[check]['success']:
            errors.append(results[check]['message'])

    response = {
        'passed': len(errors) == 0,
        'results': results
    }

    return response, errors
