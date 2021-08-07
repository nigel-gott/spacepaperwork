from django import forms
from django.core.exceptions import ValidationError

from goosetools.items.models import InventoryItem, Item, StackedInventoryItem
from goosetools.pricing.constants import PRICE_AGG_METHODS, PRICE_TYPES
from goosetools.pricing.models import DataSet
from goosetools.users.utils import filter_controlled_qs_to_viewable


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
    price_list = forms.ModelChoiceField(
        queryset=DataSet.objects.all(),
        required=True,
        empty_label=None,
        help_text="Which list of prices to use to calculate item estimate prices.",
    )
    price_to_use = forms.ChoiceField(
        choices=PRICE_TYPES,
        required=True,
        initial="lowest_sell",
        help_text="Every price can have multiple different values. For example it could"
        "Have a value for 'buy' or 'sell', in this dropdown you can choose which of "
        "these values you want to use when calculating the estimate price",
    )
    price_picking_algorithm = forms.ChoiceField(
        choices=PRICE_AGG_METHODS,
        required=True,
        initial="min",
        help_text="How to calculate estimate price from the prices found for the item"
        "in the chosen price list.",
    )
    hours_to_lookback_over_price_data = forms.IntegerField(
        required=False,
        initial=24 * 7,
        help_text="How many hours to look-back over price data when "
        "calculating the estimate price per item.",
    )
    min_price = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        initial=250000,
        required=True,
        help_text="Items with an estimate price less than this will be filtered out "
        "entirely",
    )
    overall_cut = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        label="Cut %",
        initial=35,
        help_text="A percentage to reduce every estimate price by, in effect this "
        "gives you a direct cut of the every item.",
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)
        self.fields["price_list"].queryset = filter_controlled_qs_to_viewable(
            DataSet.objects.all(), self.request, return_as_qs=True
        )
        default_price_list = DataSet.objects.get(default=True)
        self.fields["price_list"].initial = default_price_list

    def clean(self):
        cleaned_data = super().clean()
        lookback = cleaned_data["hours_to_lookback_over_price_data"]
        algo = cleaned_data["price_picking_algorithm"]
        if not lookback and algo != "latest":
            raise ValidationError(
                "You must specify how many hours worth of pricing "
                "data to look back over when using min/max/average."
            )
        return cleaned_data


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
