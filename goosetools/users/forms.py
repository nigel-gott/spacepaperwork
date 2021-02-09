from dal import autocomplete
from django import forms
from django.conf import settings
from tinymce.widgets import TinyMCE

from goosetools.user_forms.models import DynamicForm
from goosetools.users.fields import TimeZoneFormField
from goosetools.users.models import (
    Character,
    Corp,
    DiscordRole,
    GoosePermission,
    GooseUser,
)


class AuthConfigForm(forms.Form):
    code_of_conduct = forms.CharField(
        widget=TinyMCE(attrs={"cols": 80, "rows": 30}), required=False
    )


class SignupFormWithTimezone(forms.Form):
    ingame_name = forms.CharField(
        help_text="The EXACT IN GAME name of your SINGLE MAIN CHARACTER. Once approved you will be able to auth alts under Settings->Characters."
    )
    existing_character = forms.ModelChoiceField(
        queryset=Character.objects.all(),
        help_text="You already have characters in GooseTools, select which one will be applying to this corp or leave blank and fill in In Game Name for a new character.",
    )
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

    def _disable_field(self, field_name):
        self.fields.pop(field_name)

    def __init__(self, *args, **kwargs):
        existing_characters = kwargs.pop("existing_characters")
        super().__init__(*args, **kwargs)

        if not settings.GOOSEFLOCK_FEATURES:
            self._disable_field("prefered_pronouns")

        self.fields["existing_character"].queryset = existing_characters
        if existing_characters.count() == 0:
            self._disable_field(
                "existing_character",
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
        queryset=Character.objects.all(), initial=0, required=False
    )


class UserApplicationUpdateForm(forms.Form):
    notes = forms.CharField(required=False)


class AddEditCharacterForm(forms.Form):
    ingame_name = forms.CharField()
    corp = forms.ModelChoiceField(queryset=Corp.objects.all(), initial=0)


class AdminEditCharacterForm(forms.Form):
    ingame_name = forms.CharField()
    corp = forms.ModelChoiceField(queryset=Corp.objects.all(), initial=0)
    gooseuser = forms.ModelChoiceField(
        queryset=GooseUser.objects.all(),
        widget=autocomplete.ModelSelect2(url="username-autocomplete"),
    )


class AdminEditUserForm(forms.Form):
    notes = forms.CharField()
    status = forms.ChoiceField(
        choices=GooseUser.USER_STATUS_CHOICES,
    )


class CorpForm(forms.Form):
    full_name = forms.CharField()
    description = forms.CharField(
        help_text="This description will be shown to users when they are deciding which corp to apply for.",
        required=False,
    )
    public_corp = forms.BooleanField(
        help_text="Anyone regardless of discord roles can apply for this corp if ticked.",
        required=False,
    )
    sign_up_form = forms.ModelChoiceField(
        queryset=DynamicForm.objects.all(), required=False
    )
    ticker = forms.CharField()
    discord_role_given_on_approval = forms.ModelChoiceField(
        queryset=DiscordRole.objects.all().order_by("name"), required=False
    )
    discord_roles_allowing_application = forms.ModelMultipleChoiceField(
        DiscordRole.objects.all().order_by("name"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="If any roles are ticked then the user must have one or more of those roles to apply for this corp, UNLESS the corp is public which overrides anything you set here.",
    )


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


class EditGroupForm(forms.Form):
    name = forms.CharField()
    description = forms.CharField()
    required_discord_role_id = forms.ModelChoiceField(
        queryset=DiscordRole.objects.all(), required=False
    )
    permissions = forms.ModelMultipleChoiceField(
        GoosePermission.objects.all(), widget=forms.CheckboxSelectMultiple
    )
