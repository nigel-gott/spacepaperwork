import logging
from functools import partial, wraps

import requests
from django.contrib.postgres.aggregates.general import StringAgg
from django.db import models
from django.http.response import HttpResponseForbidden
from django.utils import timezone
from rest_framework.permissions import BasePermission
from timezone_field import TimeZoneField

from goosetools.tenants.models import SiteUser

logger = logging.getLogger(__name__)


class AuthConfig(models.Model):
    signup_required = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    connected_discord_server_id = models.TextField(null=True, blank=True)
    code_of_conduct = models.TextField(null=True, blank=True)
    sign_up_introduction = models.TextField(null=True, blank=True)
    new_user_discord_role = models.TextField(null=True, blank=True)

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        if self.active:
            try:
                other_active = AuthConfig.objects.get(active=True)
                if self != other_active:
                    other_active.active = False
                    other_active.save()
            except AuthConfig.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    @staticmethod
    def get_active():
        return AuthConfig.objects.get(active=True)

    @staticmethod
    def ensure_exists():
        if AuthConfig.objects.filter(active=True).count() == 0:
            AuthConfig.objects.create(
                active=True,
                signup_required=True,
            )


class SignUpQuestion(models.Model):
    auth_config = models.ForeignKey(AuthConfig, on_delete=models.CASCADE)
    question_text = models.TextField()
    question_type = models.TextField(
        choices=[
            ("text", "text"),
            ("number", "number"),
            ("textarea", "large text area"),
            ("multichoice_dropdown", "multiple choice dropdown"),
        ]
    )


class SignUpQuestionChoice(models.Model):
    signup_question = models.ForeignKey(SignUpQuestion, on_delete=models.CASCADE)
    choice = models.TextField()
    linked_discord_role = models.TextField(blank=True, null=True)


class Corp(models.Model):
    name = models.TextField(primary_key=True)
    full_name = models.TextField(unique=True, null=True, blank=True)
    # TODO map to Discord Role
    required_discord_role = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.name)


class GooseGroup(models.Model):
    name = models.TextField(unique=True)
    description = models.TextField()
    editable = models.BooleanField(default=True)
    linked_discord_role = models.TextField(null=True, blank=True)

    def link_permission(self, permission_name: str):
        perm, _ = GoosePermission.objects.get_or_create(name=permission_name)
        GroupPermission.objects.get_or_create(group=self, permission_id=perm.id)

    def permissions(self):
        return list(
            GoosePermission.objects.filter(grouppermission__group=self)
            .all()
            .values_list("name", flat=True)
        )

    def __str__(self) -> str:
        return f"{self.name}"

    @staticmethod
    def superuser_group():
        return GooseGroup.objects.get(name=SUPERUSER_GROUP_NAME)


def has_perm(perm: str):
    """
    Decorator for views that checks that the user has the specified permission otherwise returning HttpForbidden
    """

    def outer_wrapper(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            if request.gooseuser.has_perm(perm):
                return function(request, *args, **kwargs)
            else:
                return HttpResponseForbidden()

        return wrap

    return outer_wrapper


class HasGooseToolsPerm(BasePermission):
    @staticmethod
    def of(perm):
        return partial(HasGooseToolsPerm, perm)

    def __init__(self, perm: str) -> None:
        super().__init__()
        self.perm = perm

    def has_permission(self, request, view):
        return request.gooseuser and request.gooseuser.has_perm(self.perm)


SUPERUSER_GROUP_NAME = "superuser group"
USER_ADMIN_PERMISSION = "user_admin"
USER_GROUP_ADMIN_PERMISSION = "user_group_admin"


class GoosePermission(models.Model):
    USER_PERMISSION_CHOICES = [
        (
            "basic_access",
            "Able to Apply to join and view the home page and other basic registered user pages",
        ),
        ("loot_tracker", "Able to use the loot tracker"),
        (
            "loot_tracker_admin",
            "Automatically an admin in every fleet and able to do loot buyback",
        ),
        (
            USER_ADMIN_PERMISSION,
            "Able to approve user applications and manage users",
        ),
        (
            USER_GROUP_ADMIN_PERMISSION,
            "Able to edit/add user groups and their permissions",
        ),
        (
            "single_corp_admin",
            "Able to approve corp applications for a specific corp",
        ),
        (
            "all_corp_admin",
            "Able to approve corp applications for all corps and manage characters in that corp",
        ),
        ("ship_orderer", "Able to place ship orders"),
        ("free_ship_orderer", "Able to place free ship orders"),
        ("ship_order_admin", "Able to claim and work on ship orders"),
        (
            "ship_order_price_admin",
            "Able to add/remove ship types and set if they are free or not",
        ),
    ]
    name = models.TextField(unique=True, choices=USER_PERMISSION_CHOICES)
    description = models.TextField()
    corp = models.OneToOneField(Corp, on_delete=models.CASCADE, null=True, blank=True)

    @staticmethod
    def ensure_populated():
        superuser_group, _ = GooseGroup.objects.update_or_create(
            name=SUPERUSER_GROUP_NAME,
            defaults={
                "description": "An uneditable group which has all goosetool permissions.",
                "editable": False,
            },
        )
        for choice, description in GoosePermission.USER_PERMISSION_CHOICES:
            GoosePermission.objects.update_or_create(
                name=choice, defaults={"description": description}
            )
            superuser_group.link_permission(choice)

    def __str__(self) -> str:
        return self.name


class GroupPermission(models.Model):
    group = models.ForeignKey(GooseGroup, on_delete=models.CASCADE)
    permission = models.ForeignKey(GoosePermission, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"Permission: {self.permission}, Group: {self.group}"


class GooseUser(models.Model):
    timezone = TimeZoneField(default="Europe/London")
    site_user = models.OneToOneField(SiteUser, on_delete=models.CASCADE)
    broker_fee = models.DecimalField(
        verbose_name="Your Broker Fee in %", max_digits=5, decimal_places=2, default=8.0
    )
    transaction_tax = models.DecimalField(
        verbose_name="Your Transaction Tax in %",
        max_digits=5,
        decimal_places=2,
        default=15.0,
    )
    default_character = models.OneToOneField(
        "users.Character", on_delete=models.CASCADE, null=True, blank=True
    )
    status = models.TextField(
        choices=[
            ("unapproved", "unapproved"),
            ("approved", "approved"),
            ("rejected", "rejected"),
        ],
        default="unapproved",
    )
    cached_username = models.TextField()
    uid = models.TextField()
    nick = models.TextField()
    avatar_hash = models.TextField()
    notes = models.TextField(null=True, blank=True)
    sa_profile = models.TextField(blank=True, null=True)
    voucher = models.ForeignKey(
        "GooseUser",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="current_vouches",
    )

    def groups(self):
        return self.groupmember_set.aggregate(
            groups=StringAgg(
                "group__name",
                delimiter=", ",
            )
        )["groups"]

    def has_perm(self, permission_name):
        # pylint: disable=no-member
        return (
            self.groupmember_set.filter(
                group__grouppermission__permission__name=permission_name
            ).count()
            > 0
        )

    def give_group(self, group):
        return GroupMember.objects.get_or_create(user=self, group=group)

    def username(self):
        return self.cached_username

    def latest_app(self):
        # pylint: disable=no-member
        userapp_query = self.userapplication_set.filter(status="unapproved")
        if userapp_query.count() == 1:
            return userapp_query.only()
        else:
            return False

    def is_approved(self):
        return self.status == "approved"

    def is_unapproved(self):
        return self.status == "unapproved"

    def is_rejected(self):
        return self.status == "rejected"

    def is_authed_and_approved(self):
        return self.site_user.is_authenticated and self.is_approved()

    def set_as_approved(self):
        self.status = "approved"
        self.save()

    def set_as_rejected(self):
        self.status = "rejected"
        self.save()

    def characters(self):
        return self.character_set.all()

    def _discord_account(self):
        return self.site_user.socialaccount_set.get(provider="discord")

    def extra_data(self):
        return self._discord_account().extra_data

    def cache_fields_from_social_account(self):
        discord_account = self._discord_account()
        self.uid = discord_account.uid
        extra_data = discord_account.extra_data
        username = extra_data.get("username")
        discriminator = extra_data.get("discriminator")
        self.cached_username = "{}#{}".format(username, discriminator)
        self.nick = self.cached_username
        if "nick" in extra_data:
            nick = extra_data["nick"]
            if nick and nick.strip():
                self.nick = nick.strip()
        self.avatar_hash = GooseUser._construct_avatar_url(
            extra_data, discord_account.uid
        )
        self.save()

    def discord_uid(self):
        return self.uid

    def discord_username(self):
        return self.cached_username

    def display_name(self):
        return self.nick

    def discord_avatar_url(self):
        return self.avatar_hash

    # default avatars look like this: https://cdn.discordapp.com/embed/avatars/3.png
    # there is a bug with discord's size selecting mechanism for these, doing 3.png?size=16 still returns a full size default avatar.
    @staticmethod
    def _has_default_avatar(avatar_hash):
        return not avatar_hash or len(str(avatar_hash)) == 1

    @staticmethod
    def _construct_avatar_url(extra_data, uid):
        avatar_hash = "avatar" in extra_data and extra_data["avatar"]
        discriminator = extra_data.get("discriminator")
        if GooseUser._has_default_avatar(avatar_hash):
            avatar_number = int(discriminator) % 5
            return f"https://cdn.discordapp.com/embed/avatars/{avatar_number}.png"
        return f"https://cdn.discordapp.com/avatars/{uid}/{avatar_hash}.png"

    def __str__(self) -> str:
        return self.display_name()


class GroupMember(models.Model):
    group = models.ForeignKey(GooseGroup, on_delete=models.CASCADE)
    user = models.ForeignKey(GooseUser, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("group", "user"),)


class UserApplication(models.Model):
    user = models.ForeignKey(GooseUser, on_delete=models.CASCADE)
    status = models.TextField(
        choices=[
            ("unapproved", "unapproved"),
            ("approved", "approved"),
            ("rejected", "rejected"),
        ],
        default="unapproved",
    )
    created_at = models.DateTimeField(default=timezone.now)
    application_notes = models.TextField(blank=True, null=True)
    ingame_name = models.TextField(blank=True, null=True)
    corp = models.ForeignKey(Corp, on_delete=models.CASCADE)

    previous_alliances = models.TextField(blank=True, null=True)
    activity = models.TextField(blank=True, null=True)
    looking_for = models.TextField(blank=True, null=True)

    @staticmethod
    def unapproved_applications():
        return UserApplication.objects.filter(status="unapproved")

    def _create_character(self):
        if self.ingame_name:
            main_char = Character(
                user=self.user,
                ingame_name=self.ingame_name,
                corp=None,
            )
            main_char.full_clean()
            main_char.save()
            CorpApplication.objects.create(
                status="unapproved",
                corp=self.corp,
                character=main_char,
            )

    def approve(self):
        self.status = "approved"
        self.user.set_as_approved()
        self._create_character()
        self.full_clean()
        DiscordGuild.try_give_guild_member_role(self.user)
        self.save()

    def reject(self):
        self.status = "rejected"
        self.user.set_as_rejected()
        self.full_clean()
        self.save()

    def __str__(self) -> str:
        return f"{self.status} User App for {self.user} made on {self.created_at}"


class DiscordGuild(models.Model):
    guild_id = models.TextField()
    member_role_id = models.TextField(null=True, blank=True)
    bot_token = models.TextField()
    active = models.BooleanField(default=False)

    @staticmethod
    def try_give_guild_member_role(user):
        try:
            guild = DiscordGuild.objects.get(active=True)
            if guild.member_role_id:
                logger.info(
                    f"Attempting to give member role: {guild.member_role_id} to {user.discord_uid()}"
                )
                DiscordGuild.try_give_role(user.discord_uid(), guild.member_role_id)
        except DiscordGuild.DoesNotExist:
            pass

    @staticmethod
    def try_give_role(uid, role_id):
        try:
            guild = DiscordGuild.objects.get(active=True)
            bot_headers = {
                "Authorization": "Bot {0}".format(guild.bot_token),
            }
            url = f"https://discord.com/api/guilds/{guild.guild_id}/members/{uid}/roles/{role_id}"
            request = requests.put(url, headers=bot_headers)
            logger.info(f"Response from {url} is {request}")
            request.raise_for_status()
        except DiscordGuild.DoesNotExist:
            pass

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        if self.active:
            try:
                other_active = DiscordGuild.objects.get(active=True)
                if self != other_active:
                    other_active.active = False
                    other_active.save()
            except DiscordGuild.DoesNotExist:
                pass
        super().save(*args, **kwargs)


class Character(models.Model):
    user = models.ForeignKey(GooseUser, on_delete=models.CASCADE)
    ingame_name = models.TextField(unique=True)
    corp = models.ForeignKey(Corp, on_delete=models.CASCADE, null=True, blank=True)

    def discord_avatar_url(self):
        return self.user.discord_avatar_url()

    def discord_username(self):
        return self.user.discord_username()

    def display_name(self):
        return self.user.display_name()

    def __str__(self):
        if self.corp:
            return f"[{self.corp}] {self.ingame_name}"
        else:
            return f"{self.ingame_name}"


class CorpApplication(models.Model):
    corp = models.ForeignKey(Corp, on_delete=models.CASCADE)
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    status = models.TextField(
        choices=[
            ("unapproved", "unapproved"),
            ("approved", "approved"),
            ("rejected", "rejected"),
        ],
        default="unapproved",
    )
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def approve(self):
        self.status = "approved"
        self.character.corp = self.corp
        self.character.save()
        self.full_clean()
        self.save()

    def reject(self):
        self.status = "rejected"
        self.full_clean()
        self.save()

    @staticmethod
    def unapproved_applications():
        return CorpApplication.objects.filter(status="unapproved")
