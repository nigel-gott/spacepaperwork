from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from goosetools.items.models import Item
from goosetools.pricing.models import (
    PRICE_LIST_API_TYPES,
    ItemMarketDataEvent,
    PriceList,
)
from goosetools.users.forms import (
    handle_permissible_entity_formset,
    setup_existing_permissible_entity_formset,
    setup_new_permissible_entity_formset,
)


class PriceListForm(forms.ModelForm):
    api_type = forms.ChoiceField(
        choices=PRICE_LIST_API_TYPES,
        label="API Type",
        help_text="Where this Price List will get it's data from.",
    )

    class Meta:
        model = PriceList
        fields = [
            "name",
            "description",
            "api_type",
            "price_type",
            "google_sheet_id",
            "google_sheet_cell_range",
            "default",
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        if kwargs["instance"]:
            instance = kwargs["instance"]
            self.formset = setup_existing_permissible_entity_formset(
                instance.owner, instance, self.request
            )
        else:
            self.formset = setup_new_permissible_entity_formset(
                self.request.gooseuser, PriceList, self.request
            )
        super().__init__(
            *args,
            **kwargs,
        )

    def clean(self):
        cleaned_data = super().clean()
        self.formset.clean()
        if cleaned_data.get("api_type") == "google_sheet":
            if not cleaned_data.get("google_sheet_id", None) or not cleaned_data.get(
                "google_sheet_cell_range", None
            ):
                raise ValidationError(
                    "You must specify a google sheet id and cell "
                    "range when creating/updating a google sheet "
                    "price list."
                )
        if not self.request.gooseuser.is_in_superuser_group() and cleaned_data.get(
            "default", False
        ):
            raise ValidationError("Only superusers can set a price list as default.")

        return cleaned_data

    def save(self, commit=True):
        new = self.instance.pk is None
        if new:
            self.instance.owner = self.request.gooseuser
        instance = super().save(commit=commit)

        handle_permissible_entity_formset(instance.owner, self.formset, instance)
        return instance


class EventForm(forms.ModelForm):
    price_list = forms.ModelChoiceField(queryset=PriceList.objects.all(), disabled=True)
    price_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "datepicker"}, format="%b %d, %Y"),
        input_formats=["%b. %d, %Y", "%b %d, %Y", "%B %d, %Y", "%B. %d, %Y"],
        required=True,
    )
    price_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"class": "timepicker"}, format="%I:%M %p"),
        input_formats=["%I:%M %p"],
        required=True,
    )
    item = forms.ModelChoiceField(
        queryset=Item.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(url="item-autocomplete"),
        required=True,
    )

    def clean_unique_user_id(self):
        return self.cleaned_data["unique_user_id"] or None

    class Meta:
        model = ItemMarketDataEvent
        fields = [
            "price_list",
            "unique_user_id",
            "item",
            "manual_override_price",
            "price_date",
            "price_time",
            "sell",
            "buy",
            "lowest_sell",
            "highest_buy",
            "volume",
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super().__init__(
            *args,
            **kwargs,
        )

    def clean(self):
        cleaned_data = super().clean()
        price_list = cleaned_data.get("price_list")
        price_date = cleaned_data.get("price_date")
        price_time = cleaned_data.get("price_time")

        if bool(price_date) != bool(price_time):
            raise ValidationError("You must fill in both of the Date and Time fields.")

        price_list.access_controller.can_edit(self.request.gooseuser, strict=True)
        return cleaned_data

    def save(self, commit=True):
        self.instance.time = timezone.make_aware(
            timezone.datetime.combine(
                self.cleaned_data["price_date"], self.cleaned_data["price_time"]
            )
        )

        return super().save(commit=commit)
