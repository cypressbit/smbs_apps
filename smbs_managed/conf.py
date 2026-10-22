"""Settings for a managed (Digitally Boosted) site installation, with defaults."""
from django.conf import settings


DEFAULTS = {
    'SSO_PUBLIC_KEY': '',            # PEM, Ed25519 public key of the core's SSO signing key
    'SSO_ISSUER': 'digitallyboosted',
    'SSO_LOGIN_REDIRECT': '/manage/',
    'SITE_PROJECT_ID': '',           # the JWT audience is f"site:{SITE_PROJECT_ID}"
    'CORE_API_URL': '',
    'CORE_API_TOKEN': '',            # shared bearer token, used in both directions
    'MANAGED_PRIVATE_PATHS': ('/manage/', '/admin/', '/account/'),
    'MANAGED_ADMIN_PATH': '/admin/',
    # Dotted path to a callable(theme_tokens) that applies a SiteSpec's theme (themes live in the host).
    'MANAGED_THEME_HANDLER': '',
}


def get(name):
    return getattr(settings, name, DEFAULTS[name])


def audience():
    return f'site:{get("SITE_PROJECT_ID")}'
