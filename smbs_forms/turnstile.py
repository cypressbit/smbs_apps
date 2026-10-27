"""
Cloudflare Turnstile for public forms. With TURNSTILE_SITE_KEY and
TURNSTILE_SECRET_KEY set, forms show the Turnstile widget instead of a CSRF
token (so pages with a form stay cacheable) and submissions are verified
server-side. Without them, forms use Django's CSRF protection as before.

A widget only works on the domains it lists in Cloudflare (10 at most on the
Free plan). TURNSTILE_DOMAINS names them, e.g. ["example-platform.com"]. On
any other host of the site (a customer's own domain), the form shows the
widget in a frame served from a host under those domains, which passes the
token back to the page (frame_url, views.turnstile_frame). Without
TURNSTILE_DOMAINS, every host uses the widget directly, as before.
"""
import logging
from urllib.parse import urlencode, urlsplit

import requests
from django.conf import settings
from django.urls import reverse


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


def domains():
    value = getattr(settings, 'TURNSTILE_DOMAINS', None) or []
    if isinstance(value, str):
        value = value.split(',')
    return [d.strip().lower().strip('.') for d in value if d.strip()]


def covers(host):
    """True if the widget works on `host` directly (no TURNSTILE_DOMAINS means every host)."""
    host = host.split(':')[0].lower()
    listed = domains()
    return not listed or any(host == d or host.endswith(f'.{d}') for d in listed)


def frame_host():
    """One of the site's own hosts (ALLOWED_HOSTS) that the widget covers, or None."""
    for host in settings.ALLOWED_HOSTS:
        host = host.lstrip('.')
        if host and '*' not in host and domains() and covers(host):
            return host
    return None


def frame_url(request):
    """The URL of the widget frame for this page, or '' when the page's host can use the widget directly."""
    if request is None or covers(request.get_host()):
        return ''
    host = frame_host()
    if not host:
        return ''
    scheme = 'https' if request.is_secure() else 'http'
    origin = f'{scheme}://{request.get_host()}'
    port = urlsplit(origin).port
    if port:  # local development
        host = f'{host}:{port}'
    return f'{scheme}://{host}{reverse("smbs_forms:turnstile")}?{urlencode({"origin": origin})}'


def allowed_parent(origin):
    """`origin` (scheme://host) if it is one of the site's own hosts, else None."""
    parts = urlsplit(origin or '')
    if parts.scheme not in ('https', 'http') or not parts.hostname or parts.path or parts.query:
        return None
    if parts.scheme == 'http' and not settings.DEBUG:
        return None
    hosts = [h.lstrip('.') for h in settings.ALLOWED_HOSTS if '*' not in h]
    return f'{parts.scheme}://{parts.netloc}' if parts.hostname in hosts else None
