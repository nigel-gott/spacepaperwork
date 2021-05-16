from dal import autocomplete
from django import forms
from django.conf import settings
from django.forms import HiddenInput, TextInput

from goosetools.users.forms import (
    handle_permissible_entity_formset,
    setup_existing_permissible_entity_formset,
    setup_new_permissible_entity_formset,
)
from goosetools.users.models import GooseUser
from goosetools.venmo.models import TRANSFER_TYPES, TransferMethod


class WithdrawForm(forms.Form):
    quantity = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        min_value=1,
        help_text=f"Please create an in-game contract to "
        f"{settings.WITHDRAW_INGAME_CHAR} for the quantity "
        "you want to withdraw before submitting this form.",
    )


class DepositForm(forms.Form):
    note = forms.CharField(
        help_text="Please upload a screenshot of your donation of isk to corp "
        "ensuring the time, corp and quantity are visible to imgur and "
        "link it in these notes. "
    )
    quantity = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        min_value=1,
    )


class TransferForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=GooseUser.objects.all(),
        widget=autocomplete.ModelSelect2(url="username-autocomplete"),
    )
    quantity = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        min_value=1,
    )


class TransferMethodTypeForm(forms.Form):
    transfer_type = forms.ChoiceField(choices=TRANSFER_TYPES)


class TransferMethodForm(forms.ModelForm):
    class Meta:
        model = TransferMethod
        fields = [
            "name",
            "transfer_type",
            "via_contract",
            "default",
            "generated_command_help_text",
            "deposit_command_format",
            "transfer_prefix_command_format",
            "transfer_user_command_format",
            "transfer_postfix_command_format",
        ]
        widgets = {
            "transfer_type": HiddenInput(),
            "via_contract": HiddenInput(),
            "generated_command_help_text": TextInput(),
            "deposit_command_format": TextInput(),
            "transfer_prefix_command_format": TextInput(),
            "transfer_user_command_format": TextInput(),
            "transfer_postfix_command_format": TextInput(),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")

        if kwargs["instance"]:
            instance = kwargs["instance"]
            transfer_type = instance.transfer_type
            self.formset = setup_existing_permissible_entity_formset(
                None, instance, self.request
            )
        elif "transfer_type" not in self.request.GET:
            raise forms.ValidationError("A transfer_type must be provided")
        else:
            transfer_type = self.request.GET["transfer_type"]
            self.formset = setup_new_permissible_entity_formset(
                None, TransferMethod, self.request
            )
        kwargs["initial"]["transfer_type"] = transfer_type
        super().__init__(
            *args,
            **kwargs,
        )
        if transfer_type == "contract":
            self.fields.pop("generated_command_help_text")
            self.fields.pop("deposit_command_format")
            self.fields.pop("transfer_prefix_command_format")
            self.fields.pop("transfer_user_command_format")
            self.fields.pop("transfer_postfix_command_format")
            kwargs["initial"]["via_contract"] = True
        elif transfer_type == "generate_command":
            self.fields.pop("via_contract")
            self.fields["deposit_command_format"].strip = False
            self.fields["transfer_prefix_command_format"].strip = False
            self.fields["transfer_user_command_format"].strip = False
            self.fields["transfer_postfix_command_format"].strip = False
        else:
            raise forms.ValidationError(
                "A valid value for transfer_type must be provided"
            )

    def clean(self):
        super().clean()
        self.formset.clean()

    def save(self, commit=True):
        instance = super().save(commit=commit)

        handle_permissible_entity_formset(None, self.formset, instance)
        return instance
