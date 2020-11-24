from django import forms

from goosetools.items.models import InventoryItem, Item, StackedInventoryItem


class EditOrderPriceForm(forms.Form):
    new_price = forms.DecimalField(max_digits=20, decimal_places=2)
    broker_fee = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Broker Fee %"
    )


class SellItemForm(forms.Form):
    def __init__(self, max_quantity_value, *args, **kwargs):
        super(SellItemForm, self).__init__(*args, **kwargs)
        self.fields["quantity"] = forms.IntegerField(
            min_value=1, max_value=max_quantity_value
        )

    transaction_tax = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Transaction Tax %"
    )
    broker_fee = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Broker Fee %"
    )
    listed_at_price = forms.CharField()


class BulkSellItemFormHead(forms.Form):
    overall_cut = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Cut %", initial=35
    )


class BulkSellItemForm(forms.Form):
    quality = forms.CharField(disabled=True, required=False)
    listed_at_price = forms.CharField()
    estimate_price = forms.DecimalField(
        max_digits=20, decimal_places=2, disabled=True, required=False
    )
    item = forms.ModelChoiceField(queryset=Item.objects.all(), disabled=True)
    inv_item = forms.ModelChoiceField(
        widget=forms.HiddenInput(),
        required=False,
        queryset=InventoryItem.objects.all(),
        disabled=True,
    )
    stack = forms.ModelChoiceField(
        widget=forms.HiddenInput(),
        required=False,
        queryset=StackedInventoryItem.objects.all(),
        disabled=True,
    )
    quantity = forms.IntegerField(disabled=True, min_value=1)


class SoldItemForm(forms.Form):
    quantity_remaining = forms.IntegerField(
        min_value=0,
        help_text="How much of the order is remaining, 0 means the order has fully sold!",
    )
