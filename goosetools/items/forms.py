from dal import autocomplete
from django import forms

from goosetools.items.models import Item


class InventoryItemForm(forms.Form):
    fleet_anom = forms.IntegerField(
        widget=forms.HiddenInput(), disabled=True, required=False
    )
    item = forms.ModelChoiceField(
        queryset=Item.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(url="item-autocomplete", forward=["faction"]),
        required=False,
    )
    quantity = forms.IntegerField(min_value=0, required=False)


class DeleteItemForm(forms.Form):
    are_you_sure = forms.BooleanField(initial=False)


class JunkItemsForm(forms.Form):
    max_price = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Items with an estimated price under this value will be moved to the junked items page where you can unjunk them afterwards if so desired.",
    )
