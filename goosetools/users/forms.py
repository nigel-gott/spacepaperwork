from allauth.socialaccount.forms import SignupForm
from dal import autocomplete
from django import forms
from django.db.models.query_utils import Q

from goosetools.users.fields import TimeZoneFormField
from goosetools.users.models import Character, Corp, DiscordUser


class SignupFormWithTimezone(SignupForm):
    previous_alliances = forms.CharField(
        help_text="Have you been in any previous alliances? If so, what alliances?"
    )
    activity = forms.CharField(
        help_text="How active would you say you are in-game and on discord?"
    )
    looking_for = forms.CharField(
        help_text="What are you looking for in a corp and how does honking make you feel?"
    )
    application_notes = forms.CharField(
        required=False,
        help_text="Please fill in with anything else relevent to your application.",
    )
    ingame_name = forms.CharField(
        help_text="The name of you main account you will be applying to Gooseflock with."
    )
    corp = forms.ModelChoiceField(
        queryset=Corp.objects.all(),
        help_text="The Gooseflock corp you wish to apply to. Please send an application in-game to this corp with the same character you have entered above after submitting this form.",
    )

    timezone = TimeZoneFormField(display_GMT_offset=True)
    transaction_tax = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        label="Transaction Tax %",
        initial=15,
        help_text="Used to calculate fees when you sell loot in goosetools.",
    )
    broker_fee = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        label="Broker Fee %",
        initial=8,
        help_text="Used to calculate fees when you sell loot in goosetools.",
    )
    default_character = forms.ModelChoiceField(
        queryset=Character.objects.all(), required=False
    )

    def _disable_field(self, field_name):
        field = self.fields[field_name]
        field.required = False
        field.widget = forms.HiddenInput()
        field.label = ""

    @staticmethod
    def corp_label_from_instance(corp):
        if corp.full_name:
            return f"[{corp}] {corp.full_name}"
        else:
            return f"[{corp}]"

    def __init__(self, *args, **kwargs):
        sociallogin = kwargs.get("sociallogin", None)
        super().__init__(*args, **kwargs)
        self.fields.pop("email")
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
            Q(required_discord_role__in=roles)
            | Q(required_discord_role__isnull=True)
            | Q(required_discord_role__exact="")
        )

        self.fields["corp"].label_from_instance = self.corp_label_from_instance
        self.fields["corp"].initial = self.fields["corp"].queryset.first()

        existing_characters = Character.objects.filter(discord_user__uid=uid)
        default_character_field = self.fields["default_character"]
        if pre_approved and existing_characters.count() > 0:
            default_character_field.queryset = existing_characters
        else:
            default_character_field.queryset = Character.objects.none()
            self._disable_field("default_character")

        if pre_approved:
            self._disable_field("previous_alliances")
            self._disable_field("activity")
            self._disable_field("looking_for")
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


class UserApplicationUpdateForm(forms.Form):
    notes = forms.CharField(required=False)


class AddEditCharacterForm(forms.Form):
    ingame_name = forms.CharField()
    corp = forms.ModelChoiceField(queryset=Corp.objects.all(), initial=0)


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
