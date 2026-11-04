from smbs_apps.smbs_pages import fields
from smbs_apps.smbs_pages.widgets import BaseWidget


class CartLink(BaseWidget):
    """Defined here so every host can validate it; the template and the shop's pages are the host's."""
    key = 'cart_link'
    NAME = 'Cart'
    category = 'commerce'
    icon = 'bag'
    description = 'Links to the shop and the cart (with how many items are in it). Put it in the header.'
    ai_hint = 'Only on shop websites, in the header.'
    capability = 'shop'
    template = 'smbs_widgets/v2/cart_link.html'

    class Props(fields.Schema):
        shop_label = fields.Text(max_length=30, required=False, default='Shop', label='Shop link',
                                 help_text='Empty hides the link to the shop.')
        label = fields.Text(max_length=30, required=False, default='Cart', label='Cart link')
        align = fields.Choice(['end', 'start', 'center'], label='Align')
