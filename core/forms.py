from allauth.socialaccount.forms import SignupForm
from django import forms

from .fields import TimeZoneFormField
from .models import *


class SignupFormWithTimezone(SignupForm):
    timezone = TimeZoneFormField(display_GMT_offset=True)

    def save(self, request):
        user = super(SignupFormWithTimezone, self).save(request)
        user.timezone = self.cleaned_data['timezone']
        user.save()
        return user


class FleetForm(forms.Form):
    fc = forms.ModelChoiceField(queryset=GooseUser.objects.all(), initial=0)
    name = forms.CharField(max_length=100)
    fleet_type = forms.ModelChoiceField(queryset=FleetType.objects.all(), initial=0)
    description = forms.CharField(required=False)
    location = forms.CharField(required=False)
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'datepicker',
        })
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'timepicker',
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'datepicker',
        })
    )
    end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'class': 'timepicker',
        })
    )


class SettingsForm(forms.ModelForm):
    timezone = TimeZoneFormField(display_GMT_offset=True)

    class Meta:
        model = GooseUser
        fields = ["timezone"]
