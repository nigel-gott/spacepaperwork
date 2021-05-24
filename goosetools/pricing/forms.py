from django import forms

from goosetools.pricing.models import PriceList
from goosetools.users.forms import (
    handle_permissible_entity_formset,
    setup_existing_permissible_entity_formset,
    setup_new_permissible_entity_formset,
)
from goosetools.venmo.models import TransferMethod


class PriceListForm(forms.ModelForm):
    class Meta:
        model = PriceList
        fields = [
            "name",
            "description",
            "api_type",
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
                self.request.gooseuser, TransferMethod, self.request
            )
        super().__init__(
            *args,
            **kwargs,
        )

    def clean(self):
        super().clean()
        self.formset.clean()

    def save(self, commit=True):
        instance = super().save(commit=commit)

        handle_permissible_entity_formset(None, self.formset, instance)
        return instance
