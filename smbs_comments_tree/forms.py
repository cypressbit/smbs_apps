from django import forms
from django.utils.translation import gettext_lazy as _


class CommentForm(forms.ModelForm):

    model_field_name = forms.CharField()
    model_instance_id = forms.CharField()

    class Meta:
        fields = (
            'text',
            'parent',
            'model_field_name',
        )

        widgets = {
            'text': forms.Textarea(attrs={'rows': 2, 'placeholder': _('Write your comment here...')}),
            'parent': forms.HiddenInput(),
            'model_field_name': forms.HiddenInput(),
            'model_instance_id': forms.HiddenInput(),
        }
