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
from goosetools.users.models import Character, DiscordGuild, GooseUser, UserApplication


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

        super().save_user(request, sociallogin, form)
        _create_application_if_not_approved(sociallogin.user, form, request)
        _update_user_from_social_account(account, sociallogin.user, request)
        _give_pronoun_roles(account.uid, form)

    def validate_disconnect(self, account, accounts):
        raise ValidationError("Can not disconnect")


def _give_pronoun_roles(uid, form):
    prefered_pronouns = form.cleaned_data["prefered_pronouns"]
    if prefered_pronouns == "they":
        DiscordGuild.try_give_role(uid, 762405572136927242)
    elif prefered_pronouns == "she":
        DiscordGuild.try_give_role(uid, 762405484614910012)
    elif prefered_pronouns == "he":
        DiscordGuild.try_give_role(uid, 762404773512740905)


def _update_user_from_social_account(account, gooseuser, request):
    _update_gooseuser_username_to_match_discord(account, gooseuser, request)
    try:
        guild = DiscordGuild.objects.get(active=True)
        _setup_user_groups_from_discord_guild_roles(
            gooseuser, account.extra_data, guild
        )
    except DiscordGuild.DoesNotExist:
        pass


def _update_gooseuser_username_to_match_discord(account, gooseuser, request):
    new_username = (
        account.extra_data["username"] + "#" + account.extra_data["discriminator"]
    )

    existing_user = GooseUser.objects.filter(username=new_username)
    if len(existing_user) > 0 and existing_user[0].id != gooseuser.id:
        messages.error(
            request,
            f"ERROR: There is already a user signed up to goosetools with the exact same Discord Username as you '{new_username}'. This should be impossible, please PM @thejanitor to get this fixed.",
        )
        raise ValidationError(
            f"User already exists with {new_username} username cannot change {gooseuser.username} to match."
        )

    gooseuser.username = new_username
    gooseuser.save()
