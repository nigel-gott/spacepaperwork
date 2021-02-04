from dal import autocomplete
from django import forms

from goosetools.users.models import GooseUser


class WithdrawForm(forms.Form):
    quantity = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        min_value=1,
        help_text="Please create an in-game contract to 877 Cash Now for the quantity you want to withdraw before submitting this form.",
    )


class DepositForm(forms.Form):
    note = forms.CharField(
        help_text="Please upload a screenshot of your donation of isk to corp ensuring the time, corp and quantity are visibile to imgur and link it in these notes."
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
