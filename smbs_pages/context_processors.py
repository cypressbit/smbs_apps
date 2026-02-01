from django.contrib.sites.models import Site

from smbs_apps.smbs_pages.models import Page


def get_pages(request):
    site = Site.objects.get_current()
    pages = Page.objects.filter(
        site=site,
        show_on_navigation=True,
        nav_parent__isnull=True
    ).order_by('navigation_order', 'name')
    return {
        'pages': pages
    }
