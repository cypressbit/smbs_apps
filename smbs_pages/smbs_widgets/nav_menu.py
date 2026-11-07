from django.contrib.sites.models import Site
from django.db.models import Q

from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.models import Page
from smbs_apps.smbs_pages.widgets import BaseWidget

MAX_ITEMS = 8


class NavMenu(BaseWidget):
    key = 'nav_menu'
    NAME = 'Menu'
    category = 'basic'
    icon = 'list'
    description = 'Links to your pages, kept up to date for you. Choose which pages appear in each page’s settings.'
    ai_hint = 'Lists the website’s pages by itself: write nothing here.'
    template = 'smbs_widgets/v2/nav_menu.html'

    class Props(fields.Schema):
        align = fields.Choice(['end', 'center', 'start'], label='Position')

    def get_context_data(self):
        context = super().get_context_data()
        pages = (Page.objects.filter(site=Site.objects.get_current(), active=True, show_on_navigation=True,
                                     nav_parent__isnull=True)
                 # A document page visitors can see: published. Legacy pages show as they always have.
                 .filter(~Q(content_mode=Page.ContentMode.DOCUMENT) | Q(published_revision__isnull=False))
                 .order_by('navigation_order', 'name')[:MAX_ITEMS])
        request = context.get('request')
        path = request.path if request else ''
        context['items'] = [{'name': page.name, 'url': url, 'current': url == path,
                             'external': bool(page.external_url)}
                            for page in pages for url in [page.get_absolute_url()]]
        return context
