from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget, data


class FeaturedProduct(BaseWidget):
    """Defined here so every host can validate it; the product comes from the host ("shop.product")."""
    key = 'featured_product'
    NAME = 'Featured product'
    category = 'commerce'
    icon = 'bag-heart'
    description = 'One product with its photo, price and an “Add to cart” button.'
    ai_hint = 'Only on shop websites. Leave the product empty: the owner picks one of their own.'
    capability = 'shop'
    template = 'smbs_widgets/v2/featured_product.html'

    class Props(fields.Schema):
        product = fields.Text(max_length=200, required=False, label='Product',
                              help_text='The product’s name, as in Shop › Products.')
        photo_side = fields.Choice(['left', 'right'], label='Photo')

    def get_context_data(self):
        context = super().get_context_data()
        context['product'] = data('shop.product', name=(self.props.get('product') or '').strip(),
                                  editing=bool(self.context.get('editing')))
        return context
