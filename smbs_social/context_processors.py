from django.contrib.sites.models import Site

from smbs_apps.smbs_social.models import SocialSettings


def get_social_settings(request):
    site = Site.objects.get_current()
    social_settings, c = SocialSettings.objects.get_or_create(site=site)
    response = {'social_settings': social_settings}

    return response
