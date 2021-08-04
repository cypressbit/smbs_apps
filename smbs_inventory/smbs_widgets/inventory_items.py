from django.template import loader

from smbs_inventory.models import Item


class Widget:

    NAME = 'Inventory Items'

    def __init__(self, **kwargs):
        self.options = kwargs.get('options', {})

    def render(self):
        inventory_items = self.options.get('inventory_items', 6)
        items = Item.objects.filter(is_visible=True, is_featured=True)[:int(inventory_items)]
        template_file = 'smbs_widgets/inventory_items.html'
        template = loader.get_template(template_file)
        return template.render({'inventory_items': items})
