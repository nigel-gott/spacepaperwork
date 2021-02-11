from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.signals import user_logged_in
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.shortcuts import resolve_url
from django.urls import reverse

from goosetools.tenants.models import SiteUser
from goosetools.users.discord_helpers import setup_user_groups_from_discord_guild_roles
from goosetools.users.models import DiscordGuild


# pylint: disable=unused-argument
@receiver(user_logged_in)
def user_login_handler(sender, request, user, **kwargs):
    account = SocialAccount.objects.get(user=user, provider="discord")
    _update_user_from_social_account(account, user, request)


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        if request.path.rstrip("/") == reverse("account_signup").rstrip("/"):
            return False
        return True

    def get_logout_redirect_url(self, request):
        """
        Returns the default URL to redirect to after logging in.  Note
        that URLs passed explicitly (e.g. by passing along a `next`
        GET parameter) take precedence over the value returned here.
        """
        assert request.user.is_authenticated
        if request.tenant.name == "public":
            url = "tenants:splash"
        else:
            url = "core:splash"

        return resolve_url(url)

    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after logging in.  Note
        that URLs passed explicitly (e.g. by passing along a `next`
        GET parameter) take precedence over the value returned here.
        """
        assert request.user.is_authenticated
        url = request.session.pop("next_url", None)
        if not url:
            if request.tenant.name == "public":
                url = "tenants:splash"
            else:
                url = "core:splash"

        return resolve_url(url)

    def get_signup_redirect_url(self, request):
        return self.get_login_redirect_url(request)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        """
        Saves a newly signed up social login. In case of auto-signup,
        the signup form is not available.
        """
        account = sociallogin.account

        super().save_user(request, sociallogin, form)
        _update_user_from_social_account(account, sociallogin.user, request)

    def validate_disconnect(self, account, accounts):
        raise ValidationError("Can not disconnect")


def _update_user_from_social_account(account, siteuser: SiteUser, request):
    _update_username_to_match_discord(account, siteuser, request)
    if request.tenant.name != "public":
        if siteuser.has_gooseuser():
            siteuser.gooseuser.cache_fields_from_social_account()
        try:
            setup_user_groups_from_discord_guild_roles(siteuser, account.extra_data)
        except DiscordGuild.DoesNotExist:
            pass


def _update_username_to_match_discord(account, siteuser: SiteUser, request):
    new_username = (
        account.extra_data["username"] + "#" + account.extra_data["discriminator"]
    )

    existing_user = SiteUser.objects.filter(username=new_username)
    if len(existing_user) > 0 and existing_user[0].id != siteuser.id:
        messages.error(
            request,
            f"ERROR: There is already a user signed up with the exact same Discord Username as you '{new_username}'. This should be impossible, please PM @thejanitor to get this fixed.",
        )
        raise ValidationError(
            f"User already exists with {new_username} username cannot change {siteuser.username} to match."
        )

    siteuser.username = new_username
    siteuser.save()
