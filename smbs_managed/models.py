from django.conf import settings
from django.db import models
from django.utils import timezone


class ManagedUser(models.Model):
    """Links a local user to the core platform account that signed in through SSO."""
    OWNER = 'owner'
    EDITOR = 'editor'
    ROLES = [(OWNER, 'Owner'), (EDITOR, 'Editor')]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='managed_user')
    core_user_id = models.CharField(max_length=64, unique=True)
    role = models.CharField(max_length=16, choices=ROLES, default=EDITOR)
    # Digitally Boosted staff (SSO `staff` claim); the only users who may open /admin/.
    is_platform_staff = models.BooleanField(default=False)
    last_sso_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.user} ({self.role})'


class UsedToken(models.Model):
    """SSO token ids already used, so a leaked login link can't be replayed."""
    jti = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField(db_index=True)

    @classmethod
    def cleanup(cls):
        return cls.objects.filter(expires_at__lt=timezone.now()).delete()[0]
