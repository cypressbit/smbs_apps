from django.contrib.sites.models import Site

from smbs_inventory.models import InventorySettings


def inventory(request):
    site = Site.objects.get_current()
    inventory_settings = InventorySettings.objects.filter(site=site).first()
    navigation_title = getattr(inventory_settings, 'navigation_title', 'Products')
    page_title = getattr(inventory_settings, 'page_title', 'Products')
    response = {
        'inventory_navigation_title': navigation_title,
        'inventory_page_title': page_title
    }

    return response

