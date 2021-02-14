from dal import autocomplete
from django import forms

from goosetools.fleets.models import AnomType
from goosetools.items.models import System
from goosetools.users.models import Character


class LootGroupForm(forms.Form):
    OTHER_LOOT_GROUP = "Other"
    KILL_MAIL_LOOT_GROUP = "Killmail"
    ANOM_LOOT_GROUP = "Anom"
    name = forms.CharField(max_length=100, required=False)
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


class TransferProfitForm(forms.Form):
    transfer_method = forms.ChoiceField(
        choices=[
            ("contract", "Tell Recipients To Send You Contracts"),
            ("eggs", "Send Eggs to Recipients"),
        ],
        initial="eggs",
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
