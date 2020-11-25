from dal import autocomplete
from django import forms

from goosetools.industry.models import ShipOrder
from goosetools.items.models import Item
from goosetools.users.models import Character


class ShipOrderForm(forms.Form):
    recipient_character = forms.ModelChoiceField(
        label="Recipient Character",
        queryset=Character.objects.all(),
        initial=0,
    )
    ship = forms.ModelChoiceField(
        queryset=Item.all_ships(),
        initial="Vexor Navy Issue",
        widget=autocomplete.ModelSelect2(url="ship-autocomplete"),
        required=False,
    )
    payment_method = forms.ChoiceField(choices=ShipOrder.PAYMENT_METHODS)
    notes = forms.CharField(initial="", required=False)
    quantity = forms.IntegerField(min_value=1, initial=1)
