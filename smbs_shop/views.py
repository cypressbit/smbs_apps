import json

import stripe

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse

from smbs_apps.smbs_base.views import SMBSView, SMBSObjectMetadataView
from smbs_apps.smbs_shop.models import (ShopItem, ShopCart, ShopCartItem, ShopOrder,
                                        ShopOrderItem, ShopPayment, ShopSettings)
from smbs_apps.smbs_shop.forms import CheckoutForm, PaymentForm
from smbs_apps.smbs_shop.integrations.stripe import create_stripe_payment_intent
from smbs_apps.smbs_shop.integrations.paypal import create_paypal_payment


class ItemListView(SMBSView, ListView):
    model = ShopItem
    name = 'shop'
    template_name = 'smbs_shop/shopitem_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = ShopSettings.get_settings()
        context['shop_settings'] = settings
        return context


class ItemDetailView(SMBSObjectMetadataView, DetailView):
    model = ShopItem
    template_name = 'smbs_shop/shopitem_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = ShopSettings.get_settings()
        context['shop_settings'] = settings
        return context


@method_decorator(login_required, name='dispatch')
class AddToCartView(View):
    def post(self, request, item_id):
        item = get_object_or_404(ShopItem, id=item_id)
        cart, created = ShopCart.objects.get_or_create(user=request.user)
        cart_item, created = ShopCartItem.objects.get_or_create(cart=cart, item=item)
        cart_item.quantity += 1
        cart_item.save()
        return redirect('shop:cart_detail')


@method_decorator(login_required, name='dispatch')
class CartDetailView(SMBSView, ListView):
    model = ShopCartItem
    name = 'cart'
    template_name = 'smbs_shop/shopcart_detail.html'

    def get_queryset(self):
        cart = get_object_or_404(ShopCart, user=self.request.user)
        return ShopCartItem.objects.filter(cart=cart)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_object_or_404(ShopCart, user=self.request.user)
        context['cart'] = cart
        context['cart_items'] = self.get_queryset()
        return context


@method_decorator(login_required, name='dispatch')
class RemoveFromCartView(View):
    def post(self, request, cart_item_id):
        cart_item = get_object_or_404(ShopCartItem, id=cart_item_id)
        cart_item.delete()
        return redirect('shop:cart_detail')


@method_decorator(login_required, name='dispatch')
class CheckoutView(SMBSView, View):
    name = 'checkout'
    template_name = 'smbs_shop/shopcheckout.html'

    def get(self, request):
        cart = get_object_or_404(ShopCart, user=request.user)
        cart_items = ShopCartItem.objects.filter(cart=cart)
        form = CheckoutForm(cart_items=cart_items)
        return render(request, self.template_name, {'cart_items': cart_items, 'form': form})

    def post(self, request):
        cart = get_object_or_404(ShopCart, user=request.user)
        cart_items = ShopCartItem.objects.filter(cart=cart)
        form = CheckoutForm(request.POST, cart_items=cart_items)
        if form.is_valid():
            order = ShopOrder.objects.create(user=request.user, total_price=form.cleaned_data['total_price'])
            for cart_item in cart_items:
                ShopOrderItem.objects.create(order=order, item=cart_item.item, quantity=cart_item.quantity, price=cart_item.item.get_effective_price())
            cart_items.delete()
            return redirect('shop:payment', order_id=order.id)
        return render(request, self.template_name, {'cart_items': cart_items, 'form': form})


@method_decorator(login_required, name='dispatch')
class PaymentView(SMBSView, View):
    name = 'payment'
    template_name = 'smbs_shop/shoppayment.html'

    def get(self, request, order_id):
        order = get_object_or_404(ShopOrder, id=order_id)
        form = PaymentForm()
        shop_settings = ShopSettings.get_settings()
        return render(request, self.template_name, {
            'order': order,
            'form': form,
            'stripe_public_key': shop_settings.stripe_publishable_key,
        })

    def post(self, request, order_id):
        order = get_object_or_404(ShopOrder, id=order_id)
        data = json.loads(request.body)
        payment_method_id = data.get('payment_method_id')
        shop_settings = ShopSettings.get_settings()
        stripe.api_key = shop_settings.stripe_api_key

        if payment_method_id:
            try:
                intent = stripe.PaymentIntent.create(
                    amount=int(order.total_price * 100),  # Amount in cents
                    currency='usd',
                    payment_method=payment_method_id,
                    confirmation_method='manual',
                    confirm=True,
                    metadata={'order_id': order.id},
                )
                return JsonResponse({'client_secret': intent.client_secret})
            except stripe.error.CardError as e:
                return JsonResponse({'error': str(e)}, status=400)
        else:
            form = PaymentForm(request.POST)
            if form.is_valid():
                payment_method = form.cleaned_data['payment_method']
                if payment_method == 'paypal':
                    approval_url = create_paypal_payment(order)
                    if 'error' in approval_url:
                        return render(request, self.template_name, {'order': order, 'form': form, 'error': approval_url['error']})
                    return redirect(approval_url['approval_url'])
            return render(request, self.template_name, {'order': order, 'form': form})


@method_decorator(login_required, name='dispatch')
class PaymentSuccessView(SMBSView, View):
    name = 'payment_success'
    template_name = 'smbs_shop/shoppayment_success.html'

    def get(self, request, order_id):
        order = get_object_or_404(ShopOrder, id=order_id)
        order.status = 'completed'
        order.save()
        payment = get_object_or_404(ShopPayment, order=order)
        payment.payment_status = 'completed'
        payment.save()
        return render(request, self.template_name, {'order': order})


@method_decorator(login_required, name='dispatch')
class UserOrdersView(SMBSView, ListView):
    model = ShopOrder
    name = 'orders'
    template_name = 'smbs_shop/shopuser_orders.html'

    def get_queryset(self):
        return ShopOrder.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders'] = self.get_queryset()
        return context
