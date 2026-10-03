from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.safestring import mark_safe

from smbs_apps.smbs_base.models import BaseSettings


def base(request):
    site = Site.objects.get_current()
    base_settings = BaseSettings.objects.filter(site=site).first()
    global_metadata = getattr(base_settings, 'global_metadata', '')
    # commands.apply_theme (and the admin) always save theme/custom_css under
    # the SAME filename every time (so re-running it doesn't pile up stale
    # copies in media/), which means the URL alone never changes even when
    # the file's content does — a browser or any CDN/reverse-proxy cache in
    # front of media files would otherwise keep serving the pre-update CSS
    # indefinitely. ?v=<BaseSettings.updated timestamp> busts that: it
    # changes on every save() (TimestampModel's auto_now field), including
    # apply_theme's own save, without touching the underlying filename or
    # storage logic at all.
    cache_bust = int(base_settings.updated.timestamp()) if base_settings else 0
    custom_css = getattr(base_settings, 'custom_css', '')
    if custom_css:
        custom_css = '<link href="{}?v={}" rel="stylesheet" type="text/css">'.format(
            base_settings.custom_css.url, cache_bust
        )
    theme = getattr(base_settings, 'theme', None)
    if theme:
        theme = '{}?v={}'.format(theme.url, cache_bust)
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
