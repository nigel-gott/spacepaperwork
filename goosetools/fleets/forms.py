from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError

from goosetools.fleets.models import Fleet
from goosetools.users.models import Character, DiscordUser


def get_discord_names():
    return DiscordUser.objects.values_list("username", flat=True).distinct()


class FleetForm(forms.Form):
    fc_character = forms.ModelChoiceField(queryset=Character.objects.all(), initial=0)
    name = forms.CharField(max_length=100)
    loot_type = forms.ChoiceField(
        choices=Fleet.LOOT_TYPE_CHOICES, initial="master_looter"
    )
    gives_shares_to_alts = forms.BooleanField(
        required=False, initial=False, widget=forms.CheckboxInput(attrs={})
    )
    description = forms.CharField(required=False)
    location = forms.CharField(required=False)
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "datepicker"}, format="%b %d, %Y"),
        input_formats=["%b. %d, %Y", "%b %d, %Y"],
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"class": "timepicker"}, format="%I:%M %p"),
        input_formats=["%I:%M %p"],
    )
    expected_duration = forms.CharField(
        required=False,
        help_text="If you don't know how long guess here, otherwise fill in the two "
        "fields below.",
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "datepicker"}, format="%b %d, %Y"),
        input_formats=["%b. %d, %Y", "%b %d, %Y"],
    )
    end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={"class": "timepicker"}, format="%I:%M %p"),
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

    class Meta:
        exclude = ("discord_username",)


class JoinFleetForm(forms.Form):
    character = forms.ModelChoiceField(queryset=Character.objects.all(), initial=0)
