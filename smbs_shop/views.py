from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from smbs_apps.smbs_base.views import SMBSView, SMBSObjectMetadataView
from smbs_apps.smbs_shop.models import Item, Cart, CartItem, Order, OrderItem, Payment, ShopSettings
from smbs_apps.smbs_shop.forms import CheckoutForm, PaymentForm


class ItemListView(SMBSView, ListView):
    model = Item
    name = 'shop'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = ShopSettings.get_settings()
        context['shop_settings'] = settings
        return context


class ItemDetailView(SMBSObjectMetadataView, DetailView):
    model = Item

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = ShopSettings.get_settings()
        context['shop_settings'] = settings
        return context


@method_decorator(login_required, name='dispatch')
class AddToCartView(View):
    def post(self, request, item_id):
        item = get_object_or_404(Item, id=item_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item)
        cart_item.quantity += 1
        cart_item.save()
        return redirect('shop:cart_detail')


@method_decorator(login_required, name='dispatch')
class CartDetailView(SMBSView, ListView):
    model = CartItem
    name = 'cart'

    def get_queryset(self):
        cart = get_object_or_404(Cart, user=self.request.user)
        return CartItem.objects.filter(cart=cart)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_object_or_404(Cart, user=self.request.user)
        context['cart'] = cart
        context['cart_items'] = self.get_queryset()
        return context


@method_decorator(login_required, name='dispatch')
class RemoveFromCartView(View):
    def post(self, request, cart_item_id):
        cart_item = get_object_or_404(CartItem, id=cart_item_id)
        cart_item.delete()
        return redirect('shop:cart_detail')


@method_decorator(login_required, name='dispatch')
class CheckoutView(SMBSView, View):
    name = 'checkout'

    def get(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        form = CheckoutForm()
        return render(request, 'shop/checkout.html', {'cart_items': cart_items, 'form': form})

    def post(self, request):
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(user=request.user, total_price=form.cleaned_data['total_price'])
            cart = get_object_or_404(Cart, user=request.user)
            cart_items = CartItem.objects.filter(cart=cart)
            for cart_item in cart_items:
                OrderItem.objects.create(order=order, item=cart_item.item, quantity=cart_item.quantity, price=cart_item.item.get_effective_price())
            cart_items.delete()
            return redirect('shop:payment', order_id=order.id)
        return render(request, 'shop/checkout.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class PaymentView(SMBSView, View):
    name = 'payment'

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        form = PaymentForm()
        return render(request, 'shop/payment.html', {'order': order, 'form': form})

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        form = PaymentForm(request.POST)
        if form.is_valid():
            Payment.objects.create(order=order, amount=order.total_price, payment_method=form.cleaned_data['payment_method'], payment_status='pending')
            # Here you would integrate with the payment gateway
            return redirect('shop:payment_success', order_id=order.id)
        return render(request, 'shop/payment.html', {'order': order, 'form': form})


@method_decorator(login_required, name='dispatch')
class PaymentSuccessView(SMBSView, View):
    name = 'payment_success'

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        order.status = 'completed'
        order.save()
        payment = Payment.objects.get(order=order)
        payment.payment_status = 'completed'
        payment.save()
        return render(request, 'shop/payment_success.html', {'order': order})


@method_decorator(login_required, name='dispatch')
class UserOrdersView(SMBSView, ListView):
    model = Order
    name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders'] = self.get_queryset()
        return context