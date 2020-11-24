from allauth.socialaccount.forms import SignupForm
from dal import autocomplete
from django import forms

from goosetools.users.fields import TimeZoneFormField
from goosetools.users.models import Character


class SignupFormWithTimezone(SignupForm):
    timezone = TimeZoneFormField(display_GMT_offset=True)
    transaction_tax = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Transaction Tax %", initial=15
    )
    broker_fee = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Broker Fee %", initial=8
    )
    default_character = forms.ModelChoiceField(
        queryset=Character.objects.all(), initial=0
    )

    def __init__(self, *args, **kwargs):
        sociallogin = kwargs.get("sociallogin", None)
        super(SignupFormWithTimezone, self).__init__(*args, **kwargs)
        self.fields["default_character"].queryset = Character.objects.filter(
            discord_user__uid=sociallogin.account.uid
        )


class SettingsForm(forms.Form):
    timezone = TimeZoneFormField(display_GMT_offset=True)
    transaction_tax = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Transaction Tax %", initial=15
    )
    broker_fee = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Broker Fee %", initial=8
    )
    default_character = forms.ModelChoiceField(
        queryset=Character.objects.all(), initial=0
    )


class CharacterForm(forms.Form):
    character = forms.ModelChoiceField(
        queryset=Character.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(url="character-autocomplete"),
    )
