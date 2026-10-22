import unittest

from django.apps import apps

if not apps.is_installed('smbs_apps.smbs_managed'):
    # Only Digitally Boosted sites install this app; skip quietly elsewhere.
    raise unittest.SkipTest('smbs_managed is not installed')

import json
import time
import uuid
from unittest import mock

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from smbs_apps.smbs_managed import middleware
from smbs_apps.smbs_managed.client import CoreAPIError, CoreClient
from smbs_apps.smbs_managed.models import ManagedUser, UsedToken


def _keypair():
    private = Ed25519PrivateKey.generate()
    public_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    return private, public_pem


PRIVATE_KEY, PUBLIC_PEM = _keypair()
OTHER_KEY, _ = _keypair()
API_TOKEN = 'core-api-token'

MIDDLEWARE = [
    'smbs_apps.smbs_managed.middleware.HealthCheckMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'smbs_apps.smbs_managed.middleware.StaffAdminGuardMiddleware',
    'smbs_apps.smbs_managed.middleware.CacheHeadersMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

MANAGED_SETTINGS = dict(
    SSO_PUBLIC_KEY=PUBLIC_PEM, SITE_PROJECT_ID='42', CORE_API_TOKEN=API_TOKEN,
    CORE_API_URL='https://app.example.com/api/', MIDDLEWARE=MIDDLEWARE,
)


def make_token(key=PRIVATE_KEY, **overrides):
    now = int(time.time())
    claims = {
        'iss': 'digitallyboosted', 'aud': 'site:42', 'sub': '7', 'jti': uuid.uuid4().hex,
        'iat': now, 'exp': now + 120, 'email': 'owner@example.com', 'name': 'Rosa Diaz',
        'role': 'owner', 'staff': False,
    }
    claims.update(overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, key, algorithm='EdDSA')


@override_settings(**MANAGED_SETTINGS)
class SSOTests(TestCase):

    def sso(self, token, **params):
        return self.client.get('/manage/sso/', {'token': token, **params})

    def test_valid_token_logs_in_and_redirects(self):
        response = self.sso(make_token())
        self.assertRedirects(response, '/manage/', fetch_redirect_response=False)
        user = get_user_model().objects.get(username='db-7')
        self.assertEqual((user.email, user.first_name, user.last_name), ('owner@example.com', 'Rosa', 'Diaz'))
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.is_staff)
        self.assertEqual(user.managed_user.role, 'owner')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_repeat_sign_in_updates_user(self):
        self.sso(make_token())
        self.sso(make_token(email='new@example.com', role='editor'))
        user = get_user_model().objects.get(username='db-7')
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(ManagedUser.objects.get().role, 'editor')

    def test_rejected_tokens(self):
        now = int(time.time())
        cases = {
            'wrong audience': make_token(aud='site:43'),
            'wrong issuer': make_token(iss='someone-else'),
            'expired': make_token(iat=now - 600, exp=now - 300),
            'too long-lived': make_token(exp=now + 3600),
            'bad signature': make_token(key=OTHER_KEY),
            'missing jti': make_token(jti=None),
            'missing sub': make_token(sub=None),
            'unknown role': make_token(role='admin'),
            'garbage': 'not-a-jwt',
        }
        for name, token in cases.items():
            with self.subTest(name):
                self.assertEqual(self.sso(token).status_code, 403)
        self.assertFalse(get_user_model().objects.exists())

    def test_reused_token_is_rejected(self):
        token = make_token()
        self.assertEqual(self.sso(token).status_code, 302)
        self.client.logout()
        self.assertEqual(self.sso(token).status_code, 403)

    def test_safe_next_is_followed(self):
        response = self.sso(make_token(), next='/manage/pages/')
        self.assertRedirects(response, '/manage/pages/', fetch_redirect_response=False)

    def test_open_redirect_is_blocked(self):
        for target in ('https://evil.example.com/', '//evil.example.com/', 'javascript:alert(1)'):
            with self.subTest(target):
                response = self.sso(make_token(), next=target)
                self.assertRedirects(response, '/manage/', fetch_redirect_response=False)

    @override_settings(SSO_PUBLIC_KEY='')
    def test_unconfigured_sso_rejects(self):
        self.assertEqual(self.sso(make_token()).status_code, 403)

    def test_used_token_cleanup(self):
        self.sso(make_token())
        UsedToken.objects.update(expires_at='2000-01-01T00:00:00Z')
        self.assertEqual(UsedToken.cleanup(), 1)


@override_settings(**MANAGED_SETTINGS)
class StaffAdminGuardTests(TestCase):

    def test_staff_claim_reaches_admin(self):
        self.client.get('/manage/sso/', {'token': make_token(staff=True)})
        user = get_user_model().objects.get(username='db-7')
        self.assertTrue(user.is_staff and user.is_superuser)
        self.assertEqual(self.client.get('/admin/').status_code, 200)

    def test_customer_gets_404(self):
        self.client.get('/manage/sso/', {'token': make_token()})
        self.assertEqual(self.client.get('/admin/').status_code, 404)

    def test_anonymous_cannot_see_admin_login(self):
        self.assertEqual(self.client.get('/admin/login/').status_code, 404)
        self.assertEqual(self.client.get('/admin/').status_code, 404)

    def test_local_superuser_without_sso_is_refused(self):
        user = get_user_model().objects.create_superuser('local', 'l@example.com', 'pw')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/admin/').status_code, 404)


@override_settings(**MANAGED_SETTINGS)
class MaterializeTests(TestCase):
    URL = '/manage/api/materialize/'

    def post(self, body, token=API_TOKEN):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'} if token else {}
        return self.client.post(self.URL, json.dumps(body), content_type='application/json', **headers)

    def spec(self):
        return {
            'site': {'name': 'Rosa Bakery'},
            'pages': [{
                'key': 'home', 'name': 'Home', 'slug': None,
                # Full styles: smbs_pages currently requires every style key (see report).
                'document': {'sections': [{
                    'style': {'width': 'contained', 'padding_y': 'md', 'theme': 'light', 'align': 'start'},
                    'rows': [{'style': {'gap': 'md', 'align': 'stretch'}, 'columns': [{'widgets': [
                    {'type': 'heading', 'props': {'text': 'Hi', 'level': 1, 'eyebrow': '', 'size': 'default'}},
                ]}]}]}]},
            }],
        }

    def test_requires_bearer_token(self):
        self.assertEqual(self.post(self.spec(), token=None).status_code, 401)
        self.assertEqual(self.post(self.spec(), token='wrong').status_code, 403)

    @override_settings(CORE_API_TOKEN='')
    def test_unconfigured_token_is_503(self):
        self.assertEqual(self.post(self.spec()).status_code, 503)

    def test_invalid_spec_is_400_with_errors(self):
        response = self.post({'pages': []})
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.json()['errors'])

    def test_non_json_is_400(self):
        response = self.client.post(self.URL, 'nope', content_type='application/json',
                                    HTTP_AUTHORIZATION=f'Bearer {API_TOKEN}')
        self.assertEqual(response.status_code, 400)

    def test_valid_spec_creates_published_home_page(self):
        from smbs_apps.smbs_pages.models import Page
        response = self.post(self.spec())
        self.assertEqual(response.status_code, 200, response.content)
        page = Page.objects.get(pk=response.json()['pages']['home'])
        self.assertTrue(page.is_document)
        self.assertIsNotNone(page.published_revision_id)
        self.assertEqual(Site.objects.get_current().name, 'Rosa Bakery')
        self.assertContains(self.client.get('/'), 'Hi')

    def test_wrapped_spec_without_publishing(self):
        from smbs_apps.smbs_pages.models import Page
        response = self.post({'spec': self.spec(), 'publish': False})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIsNone(Page.objects.get(slug=None).published_revision_id)

    def test_status(self):
        self.post(self.spec())
        response = self.client.get('/manage/api/status/', HTTP_AUTHORIZATION=f'Bearer {API_TOKEN}')
        self.assertEqual(response.json()['project_id'], '42')
        self.assertEqual((response.json()['pages'], response.json()['published']), (1, 1))
        self.assertEqual(self.client.get('/manage/api/status/').status_code, 401)


@override_settings(**MANAGED_SETTINGS)
class CacheHeadersTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def run_middleware(self, path, response=None, user=None):
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get(path)
        request.user = user or AnonymousUser()
        return middleware.CacheHeadersMiddleware(lambda r: response or HttpResponse('ok'))(request)

    def test_public_page_is_cacheable(self):
        self.assertEqual(self.run_middleware('/about/')['Cache-Control'], middleware.PUBLIC_CACHE)

    def test_private_paths_are_no_store(self):
        for path in ('/manage/', '/admin/', '/account/login/'):
            with self.subTest(path):
                self.assertEqual(self.run_middleware(path)['Cache-Control'], middleware.PRIVATE_CACHE)

    def test_preview_is_no_store(self):
        self.assertEqual(self.run_middleware('/?preview=abc')['Cache-Control'], middleware.PRIVATE_CACHE)

    def test_authenticated_user_is_no_store(self):
        user = get_user_model().objects.create_user('u')
        self.assertEqual(self.run_middleware('/', user=user)['Cache-Control'], middleware.PRIVATE_CACHE)

    def test_response_setting_cookie_is_not_cached(self):
        response = HttpResponse('ok')
        response.set_cookie('csrftoken', 'x')
        self.assertNotIn('Cache-Control', self.run_middleware('/', response=response))

    def test_existing_cache_control_is_kept(self):
        response = HttpResponse('ok')
        response['Cache-Control'] = 'max-age=5'
        self.assertEqual(self.run_middleware('/', response=response)['Cache-Control'], 'max-age=5')
        response = HttpResponse('ok')
        response['Cache-Control'] = 'no-store'
        self.assertEqual(self.run_middleware('/manage/', response=response)['Cache-Control'], 'no-store')

    def test_errors_are_not_cached(self):
        self.assertNotIn('Cache-Control', self.run_middleware('/', response=HttpResponse(status=404)))


@override_settings(**MANAGED_SETTINGS)
class HealthCheckTests(TestCase):

    def test_healthz_skips_host_validation(self):
        response = self.client.get('/healthz', HTTP_HOST='10.2.0.15:8000')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})


@override_settings(**MANAGED_SETTINGS)
class CoreClientTests(TestCase):

    def response(self, status=200, body=b'{"ok": true}'):
        return mock.Mock(status_code=status, content=body, text=body.decode(), json=lambda: json.loads(body))

    def test_sends_bearer_token(self):
        session = mock.Mock()
        session.request.return_value = self.response()
        result = CoreClient(session=session).published(host='rosa.digitallyboosted.com')
        self.assertEqual(result, {'ok': True})
        method, url = session.request.call_args.args
        kwargs = session.request.call_args.kwargs
        self.assertEqual((method, url), ('POST', 'https://app.example.com/api/sites/published/'))
        self.assertEqual(kwargs['headers']['Authorization'], f'Bearer {API_TOKEN}')
        self.assertEqual(kwargs['json'], {'project_id': '42', 'host': 'rosa.digitallyboosted.com'})
        self.assertEqual(kwargs['timeout'], 10)

    def test_raises_on_error(self):
        session = mock.Mock()
        session.request.return_value = self.response(status=500, body=b'boom')
        with self.assertRaises(CoreAPIError) as ctx:
            CoreClient(session=session).ai_assist({'node': 'w_1'})
        self.assertEqual(ctx.exception.status, 500)


THEMES_APPLIED = []


def record_theme(theme):
    THEMES_APPLIED.append(theme)


class ThemeHandlerTests(TestCase):

    @override_settings(CORE_API_TOKEN='secret', MANAGED_THEME_HANDLER='smbs_apps.smbs_managed.tests.record_theme')
    def test_materialize_passes_the_theme_to_the_host_handler(self):
        THEMES_APPLIED.clear()
        spec = {'theme': {'preset': 'warm'}, 'pages': [{'key': 'home', 'name': 'Home', 'slug': None}]}
        response = self.client.post('/manage/api/materialize/', json.dumps(spec), content_type='application/json',
                                    HTTP_AUTHORIZATION='Bearer secret')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(THEMES_APPLIED, [{'preset': 'warm'}])


class CsrfCacheTests(TestCase):

    def test_pages_that_use_a_csrf_token_are_private_whatever_the_middleware_order(self):
        from django.middleware.csrf import get_token
        from smbs_apps.smbs_managed.middleware import CacheHeadersMiddleware

        request = RequestFactory().get('/contact/')
        request.user = mock.Mock(is_authenticated=False)

        def view(req):
            get_token(req)
            return HttpResponse('form')
        response = CacheHeadersMiddleware(view)(request)
        self.assertEqual(response['Cache-Control'], 'private, no-store')
