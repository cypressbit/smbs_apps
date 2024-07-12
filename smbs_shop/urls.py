from django.urls import path

from smbs_apps.smbs_shop.views import ItemListView, ItemDetailView, AddToCartView, CartDetailView, RemoveFromCartView, CheckoutView, PaymentView, PaymentSuccessView, UserOrdersView

app_name = 'shop'

urlpatterns = [
    path('', ItemListView.as_view(), name='item_list'),
    path('item/<slug:slug>/', ItemDetailView.as_view(), name='item_detail'),
    path('add-to-cart/<int:item_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('cart/', CartDetailView.as_view(), name='cart_detail'),
    path('remove-from-cart/<int:cart_item_id>/', RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('payment/<int:order_id>/', PaymentView.as_view(), name='payment'),
    path('payment-success/<int:order_id>/', PaymentSuccessView.as_view(), name='payment_success'),
    path('orders/', UserOrdersView.as_view(), name='user_orders'),
]