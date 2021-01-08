from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.signals import user_logged_in
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from goosetools.users.jobs.hourly.update_discord_roles import (
    _setup_user_groups_from_discord_guild_roles,
)
from goosetools.users.models import (
    Character,
    DiscordGuild,
    DiscordUser,
    UserApplication,
)


# pylint: disable=unused-argument
@receiver(user_logged_in)
def user_login_handler(sender, request, user, **kwargs):
    account = SocialAccount.objects.get(user=user, provider="discord")
    # Keep the easier to use DiscordUser model upto date as the username, discriminator and avatar_hash fields could change between logins.
    discord_user = DiscordUser.objects.get(uid=account.uid)
    _update_discord_user(discord_user, account)
    _update_user_from_social_account(account, user)


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
        user.save()


def _create_application_if_not_approved(user, form, request):
    ingame_name = form.cleaned_data["ingame_name"]
    if Character.objects.filter(ingame_name=ingame_name).count() > 0:
        error = f"You cannot apply with an in-game name of {ingame_name} as it already exists"
        messages.error(request, error)
        raise ValidationError(error)

    application = UserApplication(
        user=user,
        status="unapproved",
        created_at=timezone.now(),
        application_notes=form.cleaned_data["application_notes"],
        ingame_name=form.cleaned_data["ingame_name"],
        previous_alliances=form.cleaned_data["previous_alliances"],
        activity=form.cleaned_data["activity"],
        looking_for=form.cleaned_data["looking_for"],
        corp=form.cleaned_data["corp"],
    )
    application.full_clean()
    application.save()


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
        _update_discord_user(discord_user, account)
        super().save_user(request, sociallogin, form)
        _create_application_if_not_approved(sociallogin.user, form, request)
        _update_user_from_social_account(account, sociallogin.user)
        _give_pronoun_roles(discord_user, form)

    def validate_disconnect(self, account, accounts):
        raise ValidationError("Can not disconnect")


def _give_pronoun_roles(discord_user, form):
    prefered_pronouns = form.cleaned_data["prefered_pronouns"]
    uid = discord_user.uid
    if prefered_pronouns == "they":
        DiscordGuild.try_give_role(uid, 762405572136927242)
    elif prefered_pronouns == "she":
        DiscordGuild.try_give_role(uid, 762405484614910012)
    elif prefered_pronouns == "he":
        DiscordGuild.try_give_role(uid, 762404773512740905)


def _update_discord_user(discord_user, account):
    discord_user.uid = account.uid
    discord_user.shortened_uid = False
    discord_user.username = (
        account.extra_data["username"] + "#" + account.extra_data["discriminator"]
    )
    discord_user.avatar_hash = account.extra_data["avatar"]

    discord_user.full_clean()
    discord_user.save()


def _update_user_from_social_account(account, gooseuser):
    try:
        guild = DiscordGuild.objects.get(active=True)
        _setup_user_groups_from_discord_guild_roles(
            gooseuser, account.extra_data, guild
        )
    except DiscordGuild.DoesNotExist:
        pass
