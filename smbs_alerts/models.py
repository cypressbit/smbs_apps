from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _
from django.db import models

from smbs_apps.smbs_base.models import TimestampModel


def get_current_site():
    site = Site.objects.get_current()
    return site.id


class Alert(TimestampModel):
    SUCCESS = 'success'
    WARNING = 'warning'
    INFO = 'info'
    DANGER = 'danger'

    ALERT_TYPES = [
        (SUCCESS, _('Success')),
        (WARNING, _('Warning')),
        (INFO, _('Info')),
        (DANGER, _('Danger')),
    ]

    TOP = 'top'
    BOTTOM = 'bottom'

    POSITIONS = [
        (TOP, _('Top')),
        (BOTTOM, _('Bottom')),
    ]

    site = models.ForeignKey(Site, on_delete=models.CASCADE, default=get_current_site)
    alert_type = models.CharField(max_length=24, choices=ALERT_TYPES, default=SUCCESS)
    title = models.CharField(max_length=128)
    content = models.TextField()
    position = models.CharField(max_length=24, choices=POSITIONS, default=TOP)
    homepage_only = models.BooleanField(default=False)
