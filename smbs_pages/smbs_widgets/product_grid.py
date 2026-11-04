from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget, data


class ProductGrid(BaseWidget):
    """Defined here so every host can validate it; the products come from the host ("shop.products")."""
    key = 'product_grid'
    NAME = 'Products'
    category = 'commerce'
    icon = 'grid-3x3-gap'
    description = 'Products from your shop, in a grid with prices and an “Add to cart” button.'
    ai_hint = 'Only on shop websites. Never invent products: the grid shows the shop’s own.'
    capability = 'shop'
    template = 'smbs_widgets/v2/product_grid.html'

    class Props(fields.Schema):
        heading = fields.Text(max_length=100, required=False, default='Shop')
        category = fields.Text(max_length=100, required=False, label='Category',
                               help_text='Optional: a category’s name, e.g. Breads. Empty shows every product.')
        count = fields.Number(min_value=1, max_value=24, default=8, label='How many')
        columns = fields.Choice(['4', '3', '2'], label='Per row')
        show_all_link = fields.Bool(default=True, label='Link to the whole shop')

    def get_context_data(self):
        context = super().get_context_data()
        context['products'] = data('shop.products', category=(self.props.get('category') or '').strip(),
                                   count=self.props['count']) or []
        return context
