from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.safestring import mark_safe

from smbs_base.models import BaseSettings


def base(request):
    site = Site.objects.get_current()
    base_settings = BaseSettings.objects.filter(site=site).first()
    global_metadata = getattr(base_settings, 'global_metadata', '')
    custom_css = getattr(base_settings, 'custom_css', '')
    if custom_css:
        custom_css = '<link href="{}" rel="stylesheet" type="text/css">'.format(base_settings.custom_css.url)
    theme = getattr(base_settings, 'theme', None)
    if theme:
        theme = theme.url
    else:
        theme = '/static/css/bootstrap.min.css'
    theme_link = '<link href="{}" rel="stylesheet" type="text/css">'.format(theme)
    logo = getattr(base_settings, 'logo', None)
    icon = getattr(base_settings, 'icon', None)
    navbar_type = getattr(base_settings, 'navbar_type', 'light')
    response = {
        'global_metadata': mark_safe(global_metadata),
        'current_site': site,
        'installed_apps': settings.INSTALLED_APPS,
        'logo': logo,
        'icon': icon,
        'theme': mark_safe(theme_link),
        'custom_css': mark_safe(custom_css),
        'navbar_type': navbar_type
    }
    return response
