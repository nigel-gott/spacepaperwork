from dal import autocomplete
from django import forms
from django.db.models.query_utils import Q

from goosetools.users.fields import TimeZoneFormField
from goosetools.users.models import Character, Corp


class SignupFormWithTimezone(forms.Form):
    prefered_pronouns = forms.ChoiceField(
        choices=[
            ("blank", "----"),
            ("they", "They/Them"),
            ("she", "She/Her"),
            ("he", "He/Him"),
        ],
        help_text="Your Prefered Pronouns, feel free not to say and leave this blank.",
        required=False,
    )
    previous_alliances = forms.CharField(
        help_text="Have you been in any previous alliances? If so, what alliances?"
    )
    activity = forms.CharField(
        help_text="How active would you say you are in-game and on discord?",
        widget=forms.Textarea(attrs={"class": "materialize-textarea"}),
    )
    looking_for = forms.CharField(
        help_text="What are you looking for in a corp and how does honking make you feel?",
        widget=forms.Textarea(attrs={"class": "materialize-textarea"}),
    )
    application_notes = forms.CharField(
        required=False,
        help_text="Please fill in with anything else relevent to your application.",
        widget=forms.Textarea(attrs={"class": "materialize-textarea"}),
    )
    ingame_name = forms.CharField(
        help_text="The EXACT name of you main account you will be applying to Gooseflock and nothing else. Once approved you will be able to auth alts under Settings->Characters."
    )
    corp = forms.ModelChoiceField(
        queryset=Corp.objects.all(),
        help_text="The Gooseflock corp you wish to apply to. Please send an application in-game to this corp with the same character you have entered above after submitting this form.",
    )

    timezone = TimeZoneFormField(
        help_text="Your Timezone",
        display_GMT_offset=True,
        widget=forms.Select(attrs={"class": "browser-default"}),
    )
    transaction_tax = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        label="Transaction Tax %",
        initial=15,
        help_text="Your ingame Transaction Tax - Used to calculate fees when you sell loot in goosetools.",
    )
    broker_fee = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        label="Broker Fee %",
        initial=8,
        help_text="Your ingame Broker Fee.",
    )

    def _disable_field(self, field_name, help_text):
        field = self.fields[field_name]
        field.help_text = help_text
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
        socialaccount = kwargs.pop("socialaccount", None)
        has_characters_already = kwargs.pop("has_characters_already", False)
        super().__init__(*args, **kwargs)

        if has_characters_already:
            self._disable_field(
                "ingame_name",
                "You already have characters in goosetools, to get them back into the corps please go to Settings->Characters after this app has been accepted",
            )

        roles = (
            socialaccount.extra_data["roles"]
            if "roles" in socialaccount.extra_data
            else []
        )
        self.fields["corp"].queryset = Corp.objects.filter(
            Q(required_discord_role__in=roles)
            | Q(required_discord_role__isnull=True)
            | Q(required_discord_role__exact="")
        )

        self.fields["corp"].label_from_instance = self.corp_label_from_instance
        self.fields["corp"].initial = self.fields["corp"].queryset.first()


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


class CharacterUserSearchForm(forms.Form):
    name = forms.CharField()


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
