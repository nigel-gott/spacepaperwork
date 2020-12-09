from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.signals import user_logged_in
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.urls import reverse

from goosetools.users.models import (
    DiscordGuild,
    DiscordRoleDjangoGroupMapping,
    DiscordUser,
)


# pylint: disable=unused-argument
@receiver(user_logged_in)
def user_login_handler(sender, request, user, **kwargs):
    account = SocialAccount.objects.get(user=user, provider="discord")
    # Keep the easier to use DiscordUser model upto date as the username, discriminator and avatar_hash fields could change between logins.
    discord_user = DiscordUser.objects.get(uid=account.uid)
    _update_user_from_social_account(discord_user, account, user)


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
        user.timezone = form.cleaned_data["timezone"]
        user.broker_fee = form.cleaned_data["broker_fee"]
        user.transaction_tax = form.cleaned_data["transaction_tax"]
        user.default_character = form.cleaned_data["default_character"]
        user.save()


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        """
        Saves a newly signed up social login. In case of auto-signup,
        the signup form is not available.
        """
        account = sociallogin.account

        existing_user_with_correct_uid = DiscordUser.objects.filter(uid=account.uid)
        if len(existing_user_with_correct_uid) == 1:
            discord_user = existing_user_with_correct_uid[0]
        else:
            discord_user = DiscordUser()

        sociallogin.user.discord_user = discord_user
        super().save_user(request, sociallogin, form)
        _update_user_from_social_account(discord_user, account, sociallogin.user)

    def validate_disconnect(self, account, accounts):
        raise ValidationError("Can not disconnect")


def _update_user_from_social_account(discord_user, account, gooseuser):

    discord_user.uid = account.uid
    discord_user.shortened_uid = False
    discord_user.username = (
        account.extra_data["username"] + "#" + account.extra_data["discriminator"]
    )
    discord_user.avatar_hash = account.extra_data["avatar"]
    _setup_user_groups_from_discord_guild_roles(gooseuser, account.extra_data)
    if discord_user.pre_approved:
        gooseuser.set_approved()

    discord_user.full_clean()
    discord_user.save()


def _setup_user_groups_from_discord_guild_roles(user, extra_data):
    try:
        guild = DiscordGuild.objects.get(active=True)
        user.groups.clear()
        if "roles" in extra_data:
            for role_id in extra_data["roles"]:
                try:
                    group_mappings = DiscordRoleDjangoGroupMapping.objects.filter(
                        role_id=role_id, guild=guild
                    )
                    for group_mapping in group_mappings.all():
                        user.groups.add(group_mapping.group)
                except DiscordRoleDjangoGroupMapping.DoesNotExist:
                    pass
    except DiscordGuild.DoesNotExist:
        pass
