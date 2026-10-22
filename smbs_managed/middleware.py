from django.db import connection
from django.http import Http404, JsonResponse

from smbs_apps.smbs_managed import conf


PUBLIC_CACHE = 'public, max-age=60, s-maxage=86400, stale-while-revalidate=86400'
PRIVATE_CACHE = 'private, no-store'


class HealthCheckMiddleware:
    """
    Answers `/healthz` before host validation runs, so Kubernetes probes that
    hit the pod IP don't need to be in ALLOWED_HOSTS. 503 if the database is down.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path != '/healthz':
            return self.get_response(request)
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception:
            return JsonResponse({'status': 'error', 'database': 'unavailable'}, status=503)
        return JsonResponse({'status': 'ok'})


class CacheHeadersMiddleware:
    """
    Marks anonymous public pages cacheable at the edge (Cloudflare) and
    everything private (panel, admin, previews, signed-in users, pages that
    use a CSRF token or set cookies) as no-store.

    Put it near the top of MIDDLEWARE (right after SecurityMiddleware) so its
    response phase runs after the session and CSRF middleware have set cookies.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        existing = response.get('Cache-Control', '')
        private = (
            request.path.startswith(tuple(conf.get('MANAGED_PRIVATE_PATHS')))
            or 'preview' in request.GET
            # A page that rendered a CSRF token is per-visitor (Django sets this in get_token();
            # CsrfViewMiddleware clears it again once it has set the cookie).
            or request.META.get('CSRF_COOKIE_NEEDS_UPDATE')
            # Anything that sets cookies (CSRF, session) is per-visitor too.
            or bool(response.cookies)
            or (hasattr(request, 'user') and request.user.is_authenticated)
        )
        if private:
            if 'no-store' not in existing and 'private' not in existing:
                response['Cache-Control'] = PRIVATE_CACHE
            return response
        if request.method in ('GET', 'HEAD') and response.status_code == 200 and not existing:
            response['Cache-Control'] = PUBLIC_CACHE
        return response


class StaffAdminGuardMiddleware:
    """
    Hides /admin/ (including its login page) from everyone except platform
    staff who signed in through SSO. Place after AuthenticationMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(conf.get('MANAGED_ADMIN_PATH')):
            user = request.user
            managed = getattr(user, 'managed_user', None) if user.is_authenticated else None
            if not (managed and managed.is_platform_staff):
                raise Http404
        return self.get_response(request)
