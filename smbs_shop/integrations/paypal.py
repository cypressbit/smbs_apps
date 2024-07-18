import paypalrestsdk

from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse

from smbs_apps.smbs_shop.models import ShopSettings, ShopOrder


def configure_paypal_sdk():
    shop_settings = ShopSettings.get_settings()
    paypalrestsdk.configure({
        "mode": shop_settings.paypal_mode,  # "sandbox" or "live"
        "client_id": shop_settings.paypal_client_id,
        "client_secret": shop_settings.paypal_client_secret
    })


def create_paypal_payment(order):
    configure_paypal_sdk()
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": settings.SITE_URL + reverse('shop:payment_success', args=[order.id]),
            "cancel_url": settings.SITE_URL + reverse('shop:payment')
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": item.item.title,
                    "sku": item.item.sku,
                    "price": str(item.item.get_effective_price()),
                    "currency": "USD",
                    "quantity": item.quantity
                } for item in order.shoporderitem_set.all()]
            },
            "amount": {
                "total": str(order.total_price),
                "currency": "USD"
            },
            "description": f"Order {order.id}"
        }]
    })

    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                return JsonResponse({'approval_url': link.href})
    else:
        return JsonResponse({'error': payment.error})


def handle_paypal_webhook(request):
    body = request.body.decode('utf-8')
    headers = {
        'PAYPAL-AUTH-ALGO': request.META.get('HTTP_PAYPAL_AUTH_ALGO'),
        'PAYPAL-CERT-URL': request.META.get('HTTP_PAYPAL_CERT_URL'),
        'PAYPAL-TRANSMISSION-ID': request.META.get('HTTP_PAYPAL_TRANSMISSION_ID'),
        'PAYPAL-TRANSMISSION-SIG': request.META.get('HTTP_PAYPAL_TRANSMISSION_SIG'),
        'PAYPAL-TRANSMISSION-TIME': request.META.get('HTTP_PAYPAL_TRANSMISSION_TIME')
    }
    shop_settings = ShopSettings.get_settings()
    webhook_id = shop_settings.paypal_webhook_id

    if paypalrestsdk.WebhookEvent.verify(headers, body, webhook_id):
        event = paypalrestsdk.WebhookEvent.deserialize(body)
        if event.event_type == 'PAYMENT.SALE.COMPLETED':
            handle_successful_payment(event)
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'error': 'Invalid signature'}, status=400)


def handle_successful_payment(event):
    order_id = event['resource']['invoice_number']
    order = ShopOrder.objects.get(id=order_id)
    order.status = 'completed'
    order.save()
    # Update payment record or perform other actions here
