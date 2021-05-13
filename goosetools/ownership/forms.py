from dal import autocomplete
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from goosetools.fleets.models import AnomType
from goosetools.items.models import System
from goosetools.users.models import Character


class LootGroupForm(forms.Form):
    OTHER_LOOT_GROUP = "Other"
    KILL_MAIL_LOOT_GROUP = "Killmail"
    ANOM_LOOT_GROUP = "Anom"
    name = forms.CharField(max_length=100, required=False)

    minute_repeat_period = forms.IntegerField(
        min_value=5,
        help_text="Optional: set this to make a copy of the group every X minutes",
        required=False,
        initial=None,
    )

    def clean_minute_repeat_period(self):
        p = self.cleaned_data["minute_repeat_period"]
        if p and p % 5 != 0:
            raise ValidationError(
                "The minute repeat period must be a multiple of 5 minutes."
            )
        return p

    repeat_start_date = forms.DateField(
        required=False,
        help_text="The day to start repeating this group on",
        widget=forms.DateInput(attrs={"class": "datepicker"}, format="%b %d, %Y"),
        input_formats=["%b. %d, %Y", "%b %d, %Y"],
    )
    repeat_start_time = forms.TimeField(
        required=False,
        help_text="The time to start repeating this group at",
        widget=forms.TimeInput(attrs={"class": "timepicker"}, format="%I:%M %p"),
        input_formats=["%I:%M %p"],
    )

    def clean(self):
        cleaned_data = super().clean()
        repeat_start_date = cleaned_data.get("repeat_start_date")
        repeat_start_time = cleaned_data.get("repeat_start_time")
        minute_repeat_period = cleaned_data.get("minute_repeat_period")

        if bool(repeat_start_date) != bool(repeat_start_time) or bool(
            repeat_start_time
        ) != bool(minute_repeat_period):
            raise ValidationError(
                "You must fill either all of or none of minute repeat period, repeat "
                "start date and repeat start time. "
            )

    loot_source = forms.ChoiceField(
        choices=[
            (ANOM_LOOT_GROUP, ANOM_LOOT_GROUP),
            # (KILL_MAIL_LOOT_GROUP, KILL_MAIL_LOOT_GROUP),
            # (OTHER_LOOT_GROUP, OTHER_LOOT_GROUP)
        ]
    )

    anom_level = forms.ChoiceField(
        choices=[
            (1, "1"),
            (2, "2"),
            (3, "3"),
            (4, "4"),
            (5, "5"),
            (6, "6"),
            (7, "7"),
            (8, "8"),
            (9, "9"),
            (10, "10"),
        ],
        required=False,
        initial=6,
    )
    anom_type = forms.ChoiceField(
        choices=AnomType.TYPE_CHOICES, required=False, initial="Inquisitor"
    )
    anom_faction = forms.ChoiceField(
        choices=AnomType.FACTIONS, required=False, initial="Serpentis"
    )
    anom_system = forms.ModelChoiceField(
        queryset=System.objects.all(),
        initial="98Q-8O",
        widget=autocomplete.ModelSelect2(url="system-autocomplete"),
    )


class LootJoinForm(forms.Form):
    character = forms.ModelChoiceField(queryset=Character.objects.all())


class LootShareForm(forms.Form):
    character = forms.ModelChoiceField(
        required=False,
        queryset=Character.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(url="character-autocomplete"),
    )
    share_quantity = forms.IntegerField(min_value=0)
    flat_percent_cut = forms.IntegerField(
        min_value=0,
        max_value=100,
        help_text="This % cut only applies to loot from this anom and not from the entire bucket.",
    )


if settings.GOOSEFLOCK_FEATURES:
    TRANSFER_CHOICES = [
        ("contract", "Tell Recipients To Send You Contracts"),
        ("eggs", "Send Eggs to Recipients"),
    ]
    INITIAL_CHOICE = "eggs"
else:
    TRANSFER_CHOICES = [
        ("contract", "Tell Recipients To Send You Contracts"),
    ]
    INITIAL_CHOICE = "contract"


class TransferProfitForm(forms.Form):
    transfer_method = forms.ChoiceField(
        choices=TRANSFER_CHOICES,
        initial=INITIAL_CHOICE,
    )
    character_to_send_contracts_to = forms.ModelChoiceField(
        required=False,
        queryset=Character.objects.all(),
    )
    own_share_in_eggs = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Tick if you want to also move your share of the profit into eggs rather than keeping it as isk.",
    )
