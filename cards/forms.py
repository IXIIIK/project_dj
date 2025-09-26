from django import forms
from .models import Card, Showcase

class ShowcaseForm(forms.ModelForm):
    class Meta:
        model = Showcase
        fields = ["name", "slug", "domains"]


class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = [
            "showcase", "title", "price", "rate_line", "age_line",
            "btn_text", "btn_url", "fine_print", "logo",
            "order_index", "active",
        ]

    def __init__(self, *args, showcase=None, **kwargs):
        super().__init__(*args, **kwargs)
        if showcase is not None:
            self.fields["showcase"].initial = showcase
            self.fields["showcase"].widget = forms.HiddenInput()

