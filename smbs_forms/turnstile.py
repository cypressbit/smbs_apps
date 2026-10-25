"""
Cloudflare Turnstile for public forms. With TURNSTILE_SITE_KEY and
TURNSTILE_SECRET_KEY set, forms show the Turnstile widget instead of a CSRF
token (so pages with a form stay cacheable) and submissions are verified
server-side. Without them, forms use Django's CSRF protection as before.
"""
import logging

import requests
from django.conf import settings


logger = logging.getLogger(__name__)
VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
RESPONSE_FIELD = 'cf-turnstile-response'


def site_key():
    return getattr(settings, 'TURNSTILE_SITE_KEY', '') or ''


def enabled():
    return bool(site_key() and getattr(settings, 'TURNSTILE_SECRET_KEY', ''))


def verify(request):
    """True if the request carries a valid Turnstile token. Fails closed if Cloudflare can't be reached."""
    token = request.POST.get(RESPONSE_FIELD, '')
    if not token or len(token) > 2048:
        return False
    remote_ip = request.headers.get('CF-Connecting-IP') or request.META.get('REMOTE_ADDR', '')
    try:
        response = requests.post(VERIFY_URL, timeout=10, data={
            'secret': settings.TURNSTILE_SECRET_KEY, 'response': token, 'remoteip': remote_ip})
        return bool(response.json().get('success'))
    except (requests.RequestException, ValueError) as exc:
        logger.warning('Turnstile verification failed: %s', exc)
        return False
