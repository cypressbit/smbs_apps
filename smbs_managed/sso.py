"""
Single sign-on from the core platform.

The core signs a short-lived JWT (EdDSA / Ed25519) and sends the user to
`/manage/sso/?token=...`. Claims:

    iss    "digitallyboosted" (SSO_ISSUER)
    aud    "site:<SITE_PROJECT_ID>"
    sub    core user id (string)
    jti    unique token id (single use)
    iat, exp   exp - iat <= 300 seconds
    email, name
    role   "owner" | "editor"
    staff  true for Digitally Boosted staff (grants /admin/)
"""
import datetime

import jwt
from django.contrib.auth import get_user_model, login
from django.db import IntegrityError, transaction
from django.utils import timezone

from smbs_apps.smbs_managed import conf
from smbs_apps.smbs_managed.models import ManagedUser, UsedToken


LEEWAY = 60
MAX_LIFETIME = 300
REQUIRED_CLAIMS = ['exp', 'iat', 'iss', 'aud', 'sub', 'jti']
ROLES = {ManagedUser.OWNER, ManagedUser.EDITOR}


class SSOError(Exception):
    pass


def verify_token(token):
    public_key = conf.get('SSO_PUBLIC_KEY')
    if not public_key:
        raise SSOError('SSO is not configured.')
    try:
        claims = jwt.decode(
            token, public_key, algorithms=['EdDSA'],
            audience=conf.audience(), issuer=conf.get('SSO_ISSUER'),
            leeway=LEEWAY, options={'require': REQUIRED_CLAIMS},
        )
    except jwt.PyJWTError as exc:
        raise SSOError(f'Invalid token: {exc}') from exc
    if claims['exp'] - claims['iat'] > MAX_LIFETIME:
        raise SSOError('Token lifetime too long.')
    if claims.get('role', ManagedUser.EDITOR) not in ROLES:
        raise SSOError('Unknown role.')
    if not isinstance(claims['sub'], str) or not claims['sub']:
        raise SSOError('Invalid subject.')
    expires_at = datetime.datetime.fromtimestamp(claims['exp'] + LEEWAY, tz=datetime.timezone.utc)
    try:
        with transaction.atomic():
            UsedToken.objects.create(jti=str(claims['jti'])[:128], expires_at=expires_at)
    except IntegrityError:
        raise SSOError('Token already used.')
    return claims


@transaction.atomic
def login_from_claims(request, claims):
    User = get_user_model()
    staff = claims.get('staff') is True
    name = (claims.get('name') or '').strip()
    first, _, last = name.partition(' ')
    username = f'db-{claims["sub"]}'[:150]
    user = User.objects.filter(username=username).first() or User(username=username)
    user.email = claims.get('email') or ''
    user.first_name, user.last_name = first[:150], last[:150]
    user.is_staff = staff
    user.is_superuser = staff
    user.is_active = True
    user.set_unusable_password()
    user.save()
    ManagedUser.objects.update_or_create(
        core_user_id=str(claims['sub']),
        defaults={'user': user, 'role': claims.get('role', ManagedUser.EDITOR),
                  'is_platform_staff': staff, 'last_sso_at': timezone.now()},
    )
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return user
