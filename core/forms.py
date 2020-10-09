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
    name = forms.CharField(widget=forms.TextInput())
    fleet_type = forms.ModelChoiceField(queryset=FleetType.objects.all(), initial=0)
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


class SettingsForm(forms.ModelForm):
    timezone = TimeZoneFormField(display_GMT_offset=True)

    class Meta:
        model = GooseUser
        fields = ["timezone"]
