from smbs_cart.models import Cart


def cart(request):
    cart_obj = Cart.objects.get(id=request.session.get('cart_id'))
    response = {
        'cart_item_count': cart_obj.items.all().count(),
        'cart_icon': ''
    }
    return response


