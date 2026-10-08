import logging
import re
import secrets
from urllib.parse import urlencode

import requests

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from smbs_apps.smbs_oauth.models import GoogleAccount, get_google_oauth_credentials


logger = logging.getLogger('smbs-debug')

GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'
GOOGLE_OAUTH_SCOPE = 'openid email profile'
REQUEST_TIMEOUT = 10  # seconds, for calls out to Google's token/userinfo endpoints

LOGIN_URL_NAME = 'smbs_accounts:login'


def _generate_unique_username(email):
    """Derive a unique Django username from an email's local part. Google
    sign-in has no separate "choose a username" step, so this just needs to
    be stable-ish and collision-free, not pretty."""
    base = re.sub(r'[^\w.@+-]', '', email.split('@')[0]) or 'user'
    base = base[:140]  # leaves room for a numeric suffix within the 150-char max
    username = base
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f'{base}{suffix}'
    return username


class GoogleLoginRedirectView(View):
    """Starts the OAuth 2.0 Authorization Code flow: redirects to Google's
    consent screen. A plain full-page redirect, no JS — matches the rest of
    this project's server-rendered login/signup pages."""

    def get(self, request):
        client_id, _client_secret = get_google_oauth_credentials()
        if not client_id:
            messages.error(request, "Google sign-in isn't set up yet. Please use your email and password.")
            return redirect(LOGIN_URL_NAME)

        state = secrets.token_urlsafe(32)
        request.session['google_oauth_state'] = state

        next_url = request.GET.get('next', '')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            request.session['google_oauth_next'] = next_url
        else:
            request.session['google_oauth_next'] = ''

        redirect_uri = request.build_absolute_uri(reverse('smbs_oauth:google_callback'))
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': GOOGLE_OAUTH_SCOPE,
            'state': state,
            'prompt': 'select_account',
        }
        return redirect(f'{GOOGLE_AUTH_URL}?{urlencode(params)}')


class GoogleCallbackView(View):
    """Handles Google's redirect back: exchanges the code for tokens, fetches
    the profile, resolves/creates the User, and logs them in."""

    def get(self, request):
        if request.GET.get('error'):
            messages.error(request, "Google sign-in was cancelled.")
            return redirect(LOGIN_URL_NAME)

        state = request.GET.get('state')
        saved_state = request.session.pop('google_oauth_state', None)
        if not state or not saved_state or state != saved_state:
            messages.error(request, "Google sign-in failed — please try again.")
            return redirect(LOGIN_URL_NAME)

        code = request.GET.get('code')
        if not code:
            messages.error(request, "Google sign-in failed — please try again.")
            return redirect(LOGIN_URL_NAME)

        client_id, client_secret = get_google_oauth_credentials()
        if not client_id or not client_secret:
            messages.error(request, "Google sign-in isn't set up yet. Please use your email and password.")
            return redirect(LOGIN_URL_NAME)

        redirect_uri = request.build_absolute_uri(reverse('smbs_oauth:google_callback'))

        try:
            token_response = requests.post(GOOGLE_TOKEN_URL, data={
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            }, timeout=REQUEST_TIMEOUT)
            token_response.raise_for_status()
            access_token = token_response.json().get('access_token')

            userinfo_response = requests.get(GOOGLE_USERINFO_URL, headers={
                'Authorization': f'Bearer {access_token}',
            }, timeout=REQUEST_TIMEOUT)
            userinfo_response.raise_for_status()
            profile = userinfo_response.json()
        except requests.RequestException:
            logger.exception('Google OAuth token/userinfo exchange failed')
            messages.error(request, "Couldn't reach Google — please try again.")
            return redirect(LOGIN_URL_NAME)

        google_sub = profile.get('sub')
        email = profile.get('email')
        email_verified = profile.get('email_verified')
        if not google_sub or not email:
            messages.error(request, "Google didn't share the information needed to sign you in.")
            return redirect(LOGIN_URL_NAME)

        google_account = GoogleAccount.objects.filter(google_sub=google_sub).select_related('user').first()
        if google_account:
            user = google_account.user
        else:
            # Google verifies the email itself, so an existing password-based
            # account with the same (verified) email is the same person —
            # link rather than create a duplicate account.
            existing_user = User.objects.filter(email__iexact=email).first() if email_verified else None
            if existing_user:
                user = existing_user
            else:
                user = User.objects.create(
                    username=_generate_unique_username(email),
                    email=email,
                    first_name=profile.get('given_name', ''),
                    last_name=profile.get('family_name', ''),
                )
                user.set_unusable_password()
                user.save()
            GoogleAccount.objects.create(user=user, google_sub=google_sub, email=email)

        if not user.is_active:
            messages.error(request, "Your account has been deactivated by an organization administrator. Please contact support.")
            return redirect(LOGIN_URL_NAME)

        # login() requires a `backend` — authenticate() isn't called in this
        # flow (there's no password), so set it explicitly rather than rely
        # on login() falling back to the single configured backend.
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)

        next_url = request.session.pop('google_oauth_next', '') or '/'
        return redirect(next_url)
