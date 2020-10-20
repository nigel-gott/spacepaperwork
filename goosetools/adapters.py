from allauth.account import forms
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import ValidationError
from django.urls import reverse
from core.models import Character


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        if request.path.rstrip("/") == reverse("account_signup").rstrip("/"):
            return False
        return True

    def save_user(self, request, user, form, commit=True):
        """
        This is called when saving user via allauth registration.
        We override this to set additional data on user object.
        """
        # Do not persist the user yet so we pass commit=False
        # (last argument)
        user = super().save_user(request, user, form, commit=False)
        user.timezone = form.cleaned_data['timezone']
        user.broker_fee = form.cleaned_data['broker_fee']
        user.transaction_tax = form.cleaned_data['transaction_tax']
        user.default_character = form.cleaned_data['default_character']
        user.save()


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def validate_disconnect(self, account, accounts):
        raise ValidationError("Can not disconnect")


