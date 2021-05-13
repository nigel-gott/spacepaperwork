from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm

from goosetools.items.models import Item, ItemChangeProposal, ItemSubSubType


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


class ItemChangeProposalSelectForm(forms.Form):
    existing_item = forms.ModelChoiceField(
        queryset=Item.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(url="item-autocomplete"),
        required=False,
        empty_label="Propose Creating an Item",
        help_text="Leave blank if you want to propose a brand new item.",
    )


class ItemChangeProposalForm(ModelForm):
    item_type = forms.ModelChoiceField(
        queryset=ItemSubSubType.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(url="item-sub-sub-type-autocomplete"),
        required=False,
    )

    class Meta:
        model = ItemChangeProposal
        fields = [
            "change",
            "name",
            "item_type",
            "eve_echoes_market_id",
        ]

    def __init__(self, *args, **kwargs):
        self.existing_item = kwargs.pop("existing_item", None)
        super().__init__(*args, **kwargs)
        if self.existing_item:
            self.fields["change"].choices = [("update", "update"), ("delete", "delete")]
        else:
            self.fields["change"].choices = [("create", "create")]

    def clean(self):
        cleaned_data = super().clean()
        existing_item = self.existing_item
        change = cleaned_data.get("change")
        name = cleaned_data.get("name")
        item_type = cleaned_data.get("item_type")
        eve_echoes_market_id = cleaned_data.get("eve_echoes_market_id")

        if change == "delete":
            if not existing_item:
                raise ValidationError("You must select an item to delete")
        elif change == "create":
            if existing_item:
                raise ValidationError(
                    "When proposing to create an item you cannot "
                    "select an existing item"
                )
            if not name or not item_type:
                raise ValidationError(
                    "You must provide a name and item type when proposing to create "
                    "an item."
                )
        elif change == "update":
            if not existing_item:
                raise ValidationError("You must select an item to update")
            if (
                name == existing_item.name
                and item_type == existing_item.item_type
                and eve_echoes_market_id == existing_item.eve_echoes_market_id
            ):
                raise ValidationError("You must at least change one attribute")
