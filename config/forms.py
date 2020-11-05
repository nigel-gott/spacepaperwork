
from allauth.account import forms
from django.core.exceptions import ValidationError


class ChangePasswordForm(forms.ChangePasswordForm):
    def clean(self):
        raise ValidationError('You cannot change password.')


class SetPasswordForm(forms.SetPasswordForm):
    def clean(self):
        raise ValidationError('You cannot set password.')


class ResetPasswordForm(forms.ResetPasswordForm):
    def clean(self):
        raise ValidationError('You cannot reset password.')


class AddEmailForm(forms.AddEmailForm):
    def clean(self):
        raise ValidationError('You cannot add an email.')

