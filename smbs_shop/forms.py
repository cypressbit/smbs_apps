from django import forms

from smbs_apps.smbs_shop.models import ShopOrder, ShopPayment


class CheckoutForm(forms.Form):
    """
    Form for the checkout process.
    """
    total_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.HiddenInput()
    )

    # Include additional fields if needed, e.g., shipping address, etc.
    # Example:
    # shipping_address = forms.CharField(max_length=255)
    # billing_address = forms.CharField(max_length=255)
    # Additional form fields can be added here based on requirements.

    def __init__(self, *args, **kwargs):
        cart_items = kwargs.pop('cart_items', None)
        super().__init__(*args, **kwargs)
        if cart_items:
            total = sum(item.item.get_effective_price() * item.quantity for item in cart_items)
            self.fields['total_price'].initial = total


class PaymentForm(forms.ModelForm):
    """
    Form for the payment process.
    """
    PAYMENT_METHOD_CHOICES = [
        # ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
    ]
    payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES)

    class Meta:
        model = ShopPayment
        fields = ['payment_method']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].widget.attrs.update({
            'class': 'form-control',
        })
