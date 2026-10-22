import hmac
import json
import os

from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from smbs_apps.smbs_managed import conf, sso


def _bearer_error(request):
    """None if the request carries the core API token, else an error response."""
    expected = conf.get('CORE_API_TOKEN')
    if not expected:
        return JsonResponse({'error': 'Core API token is not configured.'}, status=503)
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return JsonResponse({'error': 'Missing bearer token.'}, status=401)
    if not hmac.compare_digest(header[7:].encode(), expected.encode()):
        return JsonResponse({'error': 'Invalid token.'}, status=403)
    return None


@never_cache
@require_GET
def sso_login(request):
    try:
        claims = sso.verify_token(request.GET.get('token', ''))
        sso.login_from_claims(request, claims)
    except sso.SSOError:
        response = HttpResponseForbidden('This sign-in link is invalid or has expired.')
        response['Referrer-Policy'] = 'no-referrer'
        return response
    next_url = request.GET.get('next', '')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()},
                                           require_https=request.is_secure()):
        next_url = conf.get('SSO_LOGIN_REDIRECT')
    response = HttpResponseRedirect(next_url)
    # The token is in this URL; keep it out of Referer headers.
    response['Referrer-Policy'] = 'no-referrer'
    return response


@csrf_exempt
@require_POST
def materialize(request):
    from smbs_apps.smbs_pages.documents import DocumentError, materialize as materialize_spec

    error = _bearer_error(request)
    if error:
        return error
    try:
        body = json.loads(request.body)
    except ValueError:
        return JsonResponse({'errors': [{'path': '', 'message': 'Body must be JSON.'}]}, status=400)
    if isinstance(body, dict) and 'spec' in body:
        spec, publish = body['spec'], body.get('publish', True)
    else:
        spec, publish = body, True
    try:
        result = materialize_spec(spec, publish=bool(publish))
    except DocumentError as exc:
        return JsonResponse({'errors': exc.errors}, status=400)
    return JsonResponse(result)


@require_GET
def status(request):
    from smbs_apps.smbs_pages.models import Page

    error = _bearer_error(request)
    if error:
        return error
    return JsonResponse({
        'project_id': conf.get('SITE_PROJECT_ID'),
        'pages': Page.objects.count(),
        'published': Page.objects.filter(published_revision__isnull=False).count(),
        'version': os.environ.get('APP_VERSION', ''),
    })
