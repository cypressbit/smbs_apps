from django import forms


class ReactionForm(forms.ModelForm):

    class Meta:
        fields = (
            'reaction',
        )

        widgets = {
            'reaction': forms.HiddenInput(),
        }
