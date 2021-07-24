from django import forms
from django.core.exceptions import ValidationError

from goosetools.pricing.models import PRICE_LIST_API_TYPES, PriceList
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
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=commit)

        handle_permissible_entity_formset(instance.owner, self.formset, instance)
        return instance
