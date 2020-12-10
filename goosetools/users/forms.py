from allauth.socialaccount.forms import SignupForm
from dal import autocomplete
from django import forms
from django.db.models.query_utils import Q

from goosetools.users.fields import TimeZoneFormField
from goosetools.users.models import Character, Corp, DiscordUser


class SignupFormWithTimezone(SignupForm):
    timezone = TimeZoneFormField(display_GMT_offset=True)
    transaction_tax = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Transaction Tax %", initial=15
    )
    broker_fee = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Broker Fee %", initial=8
    )
    default_character = forms.ModelChoiceField(
        queryset=Character.objects.all(), required=False
    )
    application_notes = forms.CharField(required=False)
    ingame_name = forms.CharField()
    corp = forms.ModelChoiceField(queryset=Corp.objects.all())

    def _disable_field(self, field_name):
        field = self.fields[field_name]
        field.required = False
        field.widget = forms.HiddenInput()
        field.label = ""

    def __init__(self, *args, **kwargs):
        sociallogin = kwargs.get("sociallogin", None)
        super().__init__(*args, **kwargs)
        uid = sociallogin.account.uid
        try:
            pre_approved = DiscordUser.objects.get(uid=uid).pre_approved
        except DiscordUser.DoesNotExist:
            pre_approved = False

        roles = (
            sociallogin.account.extra_data["roles"]
            if "roles" in sociallogin.account.extra_data
            else []
        )
        self.fields["corp"].queryset = Corp.objects.filter(
            Q(required_discord_role__in=roles) | Q(required_discord_role__isnull=True)
        )

        existing_characters = Character.objects.filter(discord_user__uid=uid)
        default_character_field = self.fields["default_character"]
        if pre_approved and existing_characters.count() > 0:
            default_character_field.queryset = existing_characters
        else:
            default_character_field.queryset = Character.objects.none()
            self._disable_field("default_character")

        if pre_approved:
            self._disable_field("application_notes")
            self._disable_field("ingame_name")
            self._disable_field("corp")


class SettingsForm(forms.Form):
    timezone = TimeZoneFormField(display_GMT_offset=True)
    transaction_tax = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Transaction Tax %", initial=15
    )
    broker_fee = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Broker Fee %", initial=8
    )
    default_character = forms.ModelChoiceField(
        queryset=Character.objects.all(), initial=0, required=False
    )


class CharacterForm(forms.Form):
    FACTIONS = [
        ("All", "All"),
        ("Guristas", "Guritas"),
        ("Angel", "Angel"),
        ("Blood", "Blood"),
        ("Sansha", "Sansha"),
        ("Serpentis", "Serpentis"),
    ]
    faction = forms.ChoiceField(
        choices=FACTIONS,
        required=False,
        initial="All",
        label="Item Faction Filter",
    )
    character = forms.ModelChoiceField(
        queryset=Character.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(url="character-autocomplete"),
    )
