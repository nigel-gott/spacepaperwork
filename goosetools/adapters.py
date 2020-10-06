from allauth.account import forms
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import ValidationError
from django.urls import reverse


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        if request.path.rstrip("/") == reverse("account_signup").rstrip("/"):
            return False
        return True


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def validate_disconnect(self, account, accounts):
        raise ValidationError("Can not disconnect")


