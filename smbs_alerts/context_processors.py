from django.contrib.sites.models import Site
from django.utils.safestring import mark_safe

from smbs_apps.smbs_alerts.models import Alert


def get_alerts(request):
    site = Site.objects.get_current()
    site_alerts = Alert.objects.filter(site=site)
    response = {'alerts': site_alerts}

    return response
