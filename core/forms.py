from decimal import Decimal

from allauth.socialaccount.forms import SignupForm
from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.db.models.fields import PositiveIntegerField
from djmoney.forms.fields import MoneyField

from core.models import (
    Corp,
    DiscordUser,
    InventoryItem,
    Item,
    ItemFilterGroup,
    ItemSubSubType,
    ItemSubType,
    ItemType,
    LootShare,
    StackedInventoryItem,
)

from .fields import TimeZoneFormField
from .models import Character, Fleet, FleetType, System


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


class JoinFleetForm(forms.Form):
    character = forms.ModelChoiceField(queryset=Character.objects.all(), initial=0)


def get_discord_names():
    return DiscordUser.objects.values_list("username", flat=True).distinct()


class FleetAddMemberForm(forms.Form):
    fleet = forms.IntegerField(
        widget=forms.HiddenInput(), disabled=True, required=False
    )
    discord_username = autocomplete.Select2ListCreateChoiceField(
        choice_list=get_discord_names,
        required=False,
        widget=autocomplete.ListSelect2(url="discord-username-autocomplete"),
    )
    character = forms.ModelChoiceField(
        required=False,
        queryset=Character.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(
            url="character-autocomplete", forward=["discord_username", "fleet"]
        ),
    )
    manual_discord_username = forms.CharField(
        required=False,
        help_text="Enter their Discord Username or if that is unknown use a sensible name which is the same between all this persons characters.",
    )
    manual_character = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()

        character = cleaned_data["character"]
        manual_character = cleaned_data["manual_character"]

        if manual_character and character:
            raise forms.ValidationError("Fill in one of character or manual character")

        if not manual_character and not character:
            raise forms.ValidationError("Fill in one of character or manual character")

        if (
            cleaned_data["manual_character"]
            and not cleaned_data["manual_discord_username"]
        ):
            raise forms.ValidationError(
                "You must fill in Manual Discord Username if you are adding a Manual Character"
            )

        return cleaned_data

    class Meta:
        exclude = ("discord_username",)


class FleetForm(forms.Form):
    fc_character = forms.ModelChoiceField(queryset=Character.objects.all(), initial=0)
    name = forms.CharField(max_length=100)
    fleet_type = forms.ModelChoiceField(queryset=FleetType.objects.all(), initial=0)
    loot_type = forms.ChoiceField(
        choices=Fleet.LOOT_TYPE_CHOICES, initial="master_looter"
    )
    gives_shares_to_alts = forms.BooleanField(
        required=False, initial=False, widget=forms.CheckboxInput(attrs={})
    )
    loot_was_stolen = forms.BooleanField(
        required=False, initial=False, widget=forms.CheckboxInput(attrs={})
    )
    description = forms.CharField(required=False)
    location = forms.CharField(required=False)
    start_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "class": "datepicker",
            },
            format="%b %d, %Y",
        ),
        input_formats=["%b. %d, %Y", "%b %d, %Y"],
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={
                "class": "timepicker",
            },
            format="%I:%M %p",
        ),
        input_formats=["%I:%M %p"],
    )
    expected_duration = forms.CharField(
        required=False,
        help_text="If you don't know how long guess here, otherwise fill in the two "
        "fields below.",
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "datepicker",
            },
            format="%b %d, %Y",
        ),
        input_formats=["%b. %d, %Y", "%b %d, %Y"],
    )
    end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={
                "class": "timepicker",
            },
            format="%I:%M %p",
        ),
        input_formats=["%I:%M %p"],
    )

    def clean(self):
        cleaned_data = super().clean()
        end_date = cleaned_data.get("end_date")
        end_time = cleaned_data.get("end_time")

        if bool(end_date) != bool(end_time):
            raise ValidationError(
                "You must fill in both of the End Date and End Time fields."
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


class LootGroupForm(forms.Form):
    OTHER_LOOT_GROUP = "Other"
    KILL_MAIL_LOOT_GROUP = "Killmail"
    ANOM_LOOT_GROUP = "Anom"
    loot_source = forms.ChoiceField(
        choices=[
            (ANOM_LOOT_GROUP, ANOM_LOOT_GROUP),
            # (KILL_MAIL_LOOT_GROUP, KILL_MAIL_LOOT_GROUP),
            # (OTHER_LOOT_GROUP, OTHER_LOOT_GROUP)
        ]
    )

    anom_level = forms.ChoiceField(
        choices=[
            (1, 1),
            (2, 2),
            (3, 3),
            (4, 4),
            (5, 5),
            (6, 6),
            (7, 7),
            (8, 8),
            (9, 9),
            (10, 10),
        ],
        required=False,
        initial=6
    )
    anom_type = forms.ChoiceField(choices=ItemFilterGroup.TYPE_CHOICES, required=False, initial='Inquisitor')
    anom_faction = forms.ChoiceField(choices=ItemFilterGroup.FACTIONS, required=False, initial='Serpentis')
    anom_system = forms.ModelChoiceField(
        queryset=System.objects.all(),
        initial='98Q-8O',
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

    manual_discord_username = forms.CharField(
        required=False,
        help_text="Enter their Discord Username or if that is unknown use a sensible name which is the same between all this persons characters.",
    )
    manual_character = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()

        character = cleaned_data["character"]
        manual_character = cleaned_data["manual_character"]

        if manual_character and character:
            raise forms.ValidationError("Fill in one of character or manual character")

        if not manual_character and not character:
            raise forms.ValidationError("Fill in one of character or manual character")

        if (
            cleaned_data["manual_character"]
            and not cleaned_data["manual_discord_username"]
        ):
            raise forms.ValidationError(
                "You must fill in Manual Discord Username if you are adding a Manual Character"
            )


class ItemMoveAllForm(forms.Form):
    character = forms.ModelChoiceField(
        label="Character To Contract Items To",
        queryset=Character.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(url="character-autocomplete"),
        help_text="This Person Will Recieve The Items If They Approve The Contract",
    )
    system = forms.ModelChoiceField(
        queryset=System.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(url="system-autocomplete"),
        help_text="The System Where You Made The Real In-Game Contract",
    )


class SelectFilterForm(forms.Form):
    fleet_anom = forms.IntegerField(
        widget=forms.HiddenInput(), disabled=True, required=False
    )
    item_filter_group = autocomplete.Select2ListChoiceField(
        widget=autocomplete.ListSelect2(
            url="item-filter-group-autocomplete", forward=["fleet_anom"]
        )
    )


class CharacterForm(forms.Form):
    character = forms.ModelChoiceField(
        queryset=Character.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(url="character-autocomplete"),
    )


class InventoryItemForm(forms.Form):
    item_filter_group = forms.ModelChoiceField(
        queryset=ItemFilterGroup.objects.all(), disabled=True, required=False
    )
    fleet_anom = forms.IntegerField(
        widget=forms.HiddenInput(), disabled=True, required=False
    )
    # item_type = forms.ModelChoiceField(queryset=ItemType.objects.all(), initial=0
    #                                    , widget=autocomplete.ModelSelect2(url='item-type-autocomplete'))
    # item_sub_type = forms.ModelChoiceField(queryset=ItemSubType.objects.all(), initial=0
    #                                    , widget=autocomplete.ModelSelect2(url='item-sub-type-autocomplete', forward=('item_type',)))
    # item_sub_sub_type = forms.ModelChoiceField(queryset=ItemSubSubType.objects.all(), initial=0
    #                                    , widget=autocomplete.ModelSelect2(url='item-sub-sub-type-autocomplete', forward=('item_type','item_sub_type',)))
    item = forms.ModelChoiceField(
        queryset=Item.objects.all(),
        initial=0,
        widget=autocomplete.ModelSelect2(url="item-autocomplete"),
        required=False,
    )
    #    forward=('item_type','item_sub_type','item_sub_sub_type',)))
    quantity = forms.IntegerField(min_value=0, required=False)


class DeleteItemForm(forms.Form):
    are_you_sure = forms.BooleanField(initial=False)


class EditOrderPriceForm(forms.Form):
    new_price = forms.DecimalField(max_digits=20, decimal_places=2)
    broker_fee = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Broker Fee %"
    )


class SellItemForm(forms.Form):
    transaction_tax = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Transaction Tax %"
    )
    broker_fee = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Broker Fee %"
    )
    listed_at_price = forms.CharField()


class BulkSellItemFormHead(forms.Form):
    overall_cut = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Cut %", initial=35
    )


class BulkSellItemForm(forms.Form):
    quality = forms.CharField(disabled=True, required=False)
    listed_at_price = forms.CharField()
    estimate_price = forms.DecimalField(
        max_digits=20, decimal_places=2, disabled=True, required=False
    )
    item = forms.ModelChoiceField(queryset=Item.objects.all(), disabled=True)
    inv_item = forms.ModelChoiceField(
        widget=forms.HiddenInput(),
        required=False,
        queryset=InventoryItem.objects.all(),
        disabled=True,
    )
    stack = forms.ModelChoiceField(
        widget=forms.HiddenInput(),
        required=False,
        queryset=StackedInventoryItem.objects.all(),
        disabled=True,
    )
    quantity = forms.IntegerField(disabled=True, min_value=1)


class SoldItemForm(forms.Form):
    quantity_remaining = forms.IntegerField(
        min_value=0,
        help_text="How much of the order is remaining, 0 means the order has fully sold!",
    )


class DepositEggsForm(forms.Form):
    deposit_command = forms.CharField(disabled=True, required=False)
