from allauth.socialaccount.forms import SignupForm
from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError

from .fields import TimeZoneFormField
from .models import Character, FleetType, GooseUser, AnomType, System
from core.models import Corp, DiscordUser, Item, ItemSubSubType, ItemSubType, ItemType, LootShare
from djmoney.forms.fields import MoneyField


class SignupFormWithTimezone(SignupForm):
    timezone = TimeZoneFormField(display_GMT_offset=True)
    transaction_tax = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Transaction Tax %", required=False, initial=15)
    broker_fee = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Broker Fee %", required=False, initial=8)
    default_character = forms.ModelChoiceField(
        queryset=Character.objects.all(), initial=0)

    def __init__(self, *args, **kwargs):
        sociallogin = kwargs.get('sociallogin', None)
        super(SignupFormWithTimezone, self).__init__(*args, **kwargs)
        if sociallogin:
            self.fields['default_character'].queryset = sociallogin.user.characters()


class JoinFleetForm(forms.Form):
    character = forms.ModelChoiceField(
        queryset=Character.objects.all(), initial=0)


def get_discord_names():
    return DiscordUser.objects.values_list('username', flat=True).distinct()


class FleetAddMemberForm(forms.Form):
    fleet = forms.IntegerField(widget=forms.HiddenInput(), disabled=True, required=False)
    discord_username = autocomplete.Select2ListCreateChoiceField(choice_list=get_discord_names,
                                                                 required=False,
                                                                 widget=autocomplete.ListSelect2(
                                                                     url='discord-username-autocomplete'))
    character = forms.ModelChoiceField(required=False, queryset=Character.objects.all(), initial=0, widget=autocomplete.ModelSelect2(url='character-autocomplete',
                                                                                                                     forward=['discord_username','fleet']))
    manual_discord_username = forms.CharField(required=False)
    manual_character = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()

        character = cleaned_data['character']
        manual_character = cleaned_data['manual_character']

        if bool(character) == bool(manual_character):
            raise forms.ValidationError('Fill in one of character or manual character')

        if cleaned_data['manual_character'] and not cleaned_data['manual_discord_username']:
            raise forms.ValidationError('You must fill in Manual Discord Username if you are adding a Manual Character')


        return cleaned_data

    class Meta:
        exclude = ('discord_username',)
    



class FleetForm(forms.Form):
    fc_character = forms.ModelChoiceField(
        queryset=Character.objects.all(), initial=0)
    name = forms.CharField(max_length=100)
    fleet_type = forms.ModelChoiceField(
        queryset=FleetType.objects.all(), initial=0)
    gives_shares_to_alts = forms.BooleanField(required=False, initial=False, widget=forms.CheckboxInput(attrs={

    }))
    description = forms.CharField(required=False)
    location = forms.CharField(required=False)
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'datepicker',
        },
            format='%b %d, %Y'
        ),
        input_formats=['%b. %d, %Y', '%b %d, %Y'],
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'timepicker',
        },
            format='%I:%M %p'
        ),
        input_formats=['%I:%M %p'],
    )
    expected_duration = forms.CharField(required=False,
                                        help_text="If you don't know how long guess here, otherwise fill in the two "
                                                  "fields below.")
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'datepicker',
        },
            format='%b %d, %Y'
        ),
        input_formats=['%b. %d, %Y', '%b %d, %Y'],
    )
    end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'class': 'timepicker',
        },
            format='%I:%M %p'
        ),
        input_formats=['%I:%M %p'],
    )

    def clean(self):
        cleaned_data = super().clean()
        end_date = cleaned_data.get("end_date")
        end_time = cleaned_data.get("end_time")

        if bool(end_date) != bool(end_time):
            raise ValidationError(
                "You must fill in both of the End Date and End Time fields."
            )


class SettingsForm(forms.ModelForm):
    timezone = TimeZoneFormField(display_GMT_offset=True)

    class Meta:
        model = GooseUser
        fields = ["timezone", "broker_fee",
                  "transaction_tax", "default_character"]


class LootGroupForm(forms.Form):
    OTHER_LOOT_GROUP = 'Other'
    KILL_MAIL_LOOT_GROUP = 'Killmail'
    ANOM_LOOT_GROUP = 'Anom'
    loot_source = forms.ChoiceField(choices=[
        (ANOM_LOOT_GROUP, ANOM_LOOT_GROUP),
        # (KILL_MAIL_LOOT_GROUP, KILL_MAIL_LOOT_GROUP),
        # (OTHER_LOOT_GROUP, OTHER_LOOT_GROUP)
    ])

    anom_level = forms.ChoiceField(choices=[
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
    ], required=False)
    anom_type = forms.ChoiceField(
        choices=AnomType.TYPE_CHOICES, required=False)
    anom_faction = forms.ChoiceField(choices=AnomType.FACTIONS, required=False)
    anom_system = forms.ModelChoiceField(queryset=System.objects.all(
    ), initial=0, widget=autocomplete.ModelSelect2(url='system-autocomplete'))

class LootJoinForm(forms.Form):
    character = forms.ModelChoiceField(queryset=Character.objects.all())

class LootShareForm(forms.Form):
    character = forms.ModelChoiceField(queryset=Character.objects.all(
    ), initial=0, widget=autocomplete.ModelSelect2(url='character-autocomplete'))
    share_quantity = forms.IntegerField(min_value=0)
    flat_percent_cut = forms.IntegerField(min_value=0, max_value=100)


class InventoryItemForm(forms.Form):
    character = forms.ModelChoiceField(queryset=Character.objects.all(
    ), initial=0, widget=autocomplete.ModelSelect2(url='character-autocomplete'))
    # item_type = forms.ModelChoiceField(queryset=ItemType.objects.all(), initial=0
    #                                    , widget=autocomplete.ModelSelect2(url='item-type-autocomplete'))
    # item_sub_type = forms.ModelChoiceField(queryset=ItemSubType.objects.all(), initial=0
    #                                    , widget=autocomplete.ModelSelect2(url='item-sub-type-autocomplete', forward=('item_type',)))
    # item_sub_sub_type = forms.ModelChoiceField(queryset=ItemSubSubType.objects.all(), initial=0
    #                                    , widget=autocomplete.ModelSelect2(url='item-sub-sub-type-autocomplete', forward=('item_type','item_sub_type',)))
    item = forms.ModelChoiceField(queryset=Item.objects.all(
    ), initial=0, widget=autocomplete.ModelSelect2(url='item-autocomplete'))
    #    forward=('item_type','item_sub_type','item_sub_sub_type',)))
    quantity = forms.IntegerField(min_value=0)

class DeleteItemForm(forms.Form):
    are_you_sure = forms.BooleanField(initial=False)


class SellItemForm(forms.Form):
    transaction_tax = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Transaction Tax %")
    broker_fee = forms.DecimalField(
        max_digits=5, decimal_places=2, label="Broker Fee %")
    listed_at_price = forms.DecimalField(max_digits=14, decimal_places=2)

class SoldItemForm(forms.Form):
    quantity_remaining = forms.IntegerField(min_value=0)

class DepositEggsForm(forms.Form):
    deposit_command = forms.CharField(disabled=True,required=False)
