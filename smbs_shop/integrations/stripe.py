import stripe

from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse

from smbs_apps.smbs_shop.models import ShopSettings, ShopOrder


def get_stripe_api_key():
    shop_settings = ShopSettings.get_settings()
    return shop_settings.stripe_api_key


def create_stripe_payment_intent(order):
    try:
        stripe.api_key = get_stripe_api_key()
        intent = stripe.PaymentIntent.create(
            amount=int(order.total_price * 100),  # Amount in cents
            currency='usd',
            payment_method_types=['card'],
            metadata={'order_id': order.id}
        )
        return intent
    except Exception as e:
        return JsonResponse({'error': str(e)})


def handle_stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    shop_settings = ShopSettings.get_settings()

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, shop_settings.stripe_webhook_secret
        )
    except ValueError as e:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_successful_payment(payment_intent)

    return JsonResponse({'status': 'success'})


def handle_successful_payment(payment_intent):
    order_id = payment_intent['metadata']['order_id']
    order = ShopOrder.objects.get(id=order_id)
    order.status = 'completed'
    order.save()
    # Update payment record or perform other actions here
