import logging
from functools import partial, wraps
from typing import List, Union

import requests
from django.conf import settings
from django.contrib.postgres.aggregates.general import StringAgg
from django.contrib.sites.models import Site
from django.db import models
from django.http.response import HttpResponseForbidden
from django.utils import timezone
from django_comments.models import Comment
from requests.exceptions import RequestException
from rest_framework.permissions import BasePermission
from timezone_field import TimeZoneField

from goosetools.notifications.notification_types import NOTIFICATION_TYPES
from goosetools.tenants.models import SiteUser
from goosetools.user_forms.models import DynamicForm

logger = logging.getLogger(__name__)


class AuthConfig(models.Model):
    active = models.BooleanField(default=True)
    code_of_conduct = models.TextField(null=True, blank=True)

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
            )


MANAGE_ROLES_DISCORD_PERMISSION = 0x10000000


class DiscordGuild(models.Model):
    guild_id = models.TextField(null=True, blank=True)
    server_name = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=False)
    connection_valid = models.BooleanField(default=False)
    discord_connection_issue = models.BooleanField(default=False)
    has_manage_roles = models.BooleanField(default=False)

    @staticmethod
    def bot_headers():
        return {
            "Authorization": "Bot {0}".format(settings.BOT_TOKEN),
        }

    def _check_discord_is_up_and_bot_valid(self):
        self.discord_connection_issue = False
        url = "https://discord.com/api/users/@me"
        try:
            bot_info_request = requests.get(url, headers=DiscordGuild.bot_headers())
            bot_info_request.raise_for_status()
        except RequestException as e:
            print("Error querying discord for bot info: " + str(e))
            self.discord_connection_issue = True
            return False
        bot_info = bot_info_request.json()
        if "id" not in bot_info or not bot_info["bot"]:
            print("Missing Id from bot info request: " + bot_info_request.text)
            self.discord_connection_issue = True
            return False
        return True

    def _check_for_permissions(self):
        self.has_manage_roles = False
        url = f"https://discord.com/api/guilds/{self.guild_id}/members/{settings.BOT_USER_ID}"
        try:
            bot_member_request = requests.get(url, headers=DiscordGuild.bot_headers())
            bot_member_request.raise_for_status()
        except RequestException as e:
            print("Error querying discord for member info: " + str(e))
        bot_member_info = bot_member_request.json()
        if "roles" not in bot_member_info:
            print("Missing roles discord bot info request: " + bot_member_request.text)
        else:
            try:
                url = f"https://discord.com/api/guilds/{self.guild_id}/roles"
                try:
                    roles_request = requests.get(
                        url, headers=DiscordGuild.bot_headers()
                    )
                    roles_request.raise_for_status()
                except RequestException as e:
                    print("Error querying discord for roles info: " + str(e))

                roles_by_id = {role["id"]: role for role in roles_request.json()}

                for role in bot_member_info["roles"]:
                    permissions = int(roles_by_id[role]["permissions"])
                    print(permissions)
                    print(permissions & MANAGE_ROLES_DISCORD_PERMISSION)
                    print(MANAGE_ROLES_DISCORD_PERMISSION)
                    self.has_manage_roles = (
                        permissions & MANAGE_ROLES_DISCORD_PERMISSION
                    ) == MANAGE_ROLES_DISCORD_PERMISSION
                    if self.has_manage_roles:
                        return
            except (ValueError, KeyError):
                print("Weird permissions from discord guild:" + bot_member_request.text)
                if roles_request and hasattr(roles_request, "text"):
                    print(roles_request.text)

    def _check_discord_guild_is_valid(self):
        self.server_name = None
        url = f"https://discord.com/api/guilds/{self.guild_id}"
        try:
            guild_info_request = requests.get(url, headers=DiscordGuild.bot_headers())
            guild_info_request.raise_for_status()
        except RequestException as e:
            print("Error querying discord for guild info: " + str(e))
            return False
        guild_info = guild_info_request.json()
        if "name" not in guild_info:
            print(
                "Missing Name from discord guild info request: "
                + guild_info_request.text
            )
            return False
        else:
            self.server_name = guild_info["name"]

        return True

    def _update_status_fields(self):
        self.connection_valid = False
        if self.guild_id:
            if (
                self._check_discord_is_up_and_bot_valid()
                and self._check_discord_guild_is_valid()
            ):
                self._check_for_permissions()
                self.connection_valid = True

    def check_valid(self):
        self._update_status_fields()
        self.save()
        if self.connection_valid:
            DiscordRole.sync_from_discord()
            NOTIFICATION_TYPES["discord_not_setup"].dismiss()
        else:
            NOTIFICATION_TYPES["discord_not_setup"].send()
        return self.connection_valid

    @staticmethod
    def get_active():
        try:
            return DiscordGuild.objects.get(active=True)
        except DiscordGuild.DoesNotExist:
            return False

    @staticmethod
    def try_give_role(uid, role_id):
        try:
            guild = DiscordGuild.objects.get(active=True)
            bot_headers = {
                "Authorization": "Bot {0}".format(settings.BOT_TOKEN),
            }
            url = f"https://discord.com/api/guilds/{guild.guild_id}/members/{uid}/roles/{role_id}"
            request = requests.put(url, headers=bot_headers)
            request.raise_for_status()
        except DiscordGuild.DoesNotExist:
            pass

    @staticmethod
    def get_roles():
        try:
            guild = DiscordGuild.objects.get(active=True)
            bot_headers = {
                "Authorization": "Bot {0}".format(settings.BOT_TOKEN),
            }
            url = f"https://discord.com/api/guilds/{guild.guild_id}"
            request = requests.get(url, headers=bot_headers)
            request.raise_for_status()
            return [(role["name"], role["id"]) for role in request.json()["roles"]]
        except DiscordGuild.DoesNotExist:
            return []

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


class DiscordRole(models.Model):
    name = models.TextField()
    role_id = models.TextField(unique=True)

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def sync_from_discord():
        all_ids = set()
        for role_name, role_id in DiscordGuild.get_roles():
            all_ids.add(role_id)
            DiscordRole.objects.update_or_create(
                role_id=role_id, defaults={"name": role_name}
            )

        DiscordRole.objects.exclude(role_id__in=all_ids).delete()

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
        ]


class GooseGroup(models.Model):
    name = models.TextField(unique=True)
    description = models.TextField()
    editable = models.BooleanField(default=True)
    manually_given = models.BooleanField(default=False)
    linked_discord_role = models.TextField(null=True, blank=True)
    required_discord_role = models.ForeignKey(
        DiscordRole, on_delete=models.SET_NULL, null=True, blank=True
    )

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


class Corp(models.Model):
    name = models.TextField(unique=True)
    full_name = models.TextField(unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    auto_approve = models.BooleanField(default=False)
    public_corp = models.BooleanField(default=False)
    sign_up_form = models.ForeignKey(
        DynamicForm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    discord_role_given_on_approval = models.ForeignKey(
        DiscordRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="corps_giving_on_approval",
    )
    manual_group_given_on_approval = models.ForeignKey(
        GooseGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    discord_roles_allowing_application = models.ManyToManyField(
        DiscordRole, related_name="corps_allowing_application"
    )

    def name_with_corp_tag(self):
        if self.full_name:
            return f"[{self.name}] {self.full_name}"
        else:
            return f"[{self.name}]"

    def __str__(self):
        return str(self.name)

    @staticmethod
    def deleted_corp():
        return Corp.objects.get(name="DELETED")

    @staticmethod
    def unknown_corp():
        return Corp.objects.get(name="UNKNOWN")

    @staticmethod
    def ensure_populated():
        Corp.objects.get_or_create(name="DELETED", full_name="DELETED")
        Corp.objects.get_or_create(name="UNKNOWN", full_name="UNKNOWN")


def has_perm(perm: Union[str, List[str]]):
    """
    Decorator for views that checks that the user has the specified permission otherwise returning HttpForbidden
    """

    def outer_wrapper(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            if request.gooseuser.has_perm(perm):
                return function(request, *args, **kwargs)
            return HttpResponseForbidden()

        return wrap

    return outer_wrapper


class HasGooseToolsPerm(BasePermission):
    @staticmethod
    def of(perm, ignore_methods=False):
        return partial(HasGooseToolsPerm, perm, ignore_methods)

    def __init__(self, perm: Union[str, List[str]], ignore_methods=False) -> None:
        super().__init__()
        self.perm = perm
        self.ignore_methods = ignore_methods or []

    def has_permission(self, request, view):
        return (
            request.method in self.ignore_methods
            or request.gooseuser
            and request.gooseuser.has_perm(self.perm)
        )


SUPERUSER_GROUP_NAME = "superuser group"
USER_ADMIN_PERMISSION = "user_admin"
USER_GROUP_ADMIN_PERMISSION = "user_group_admin"
ALL_CORP_ADMIN = "all_corp_admin"
SINGLE_CORP_ADMIN = "single_corp_admin"
SHIP_ORDER_ADMIN = "ship_order_admin"
SHIP_PRICE_ADMIN = "ship_price_admin"
SHIP_ORDERER = "ship_orderer"
FREE_SHIP_ORDERER = "free_ship_orderer"
BASIC_ACCESS = "basic_access"
LOOT_TRACKER = "loot_tracker"
LOOT_TRACKER_ADMIN = "loot_tracker_admin"
VENMO_ADMIN = "venmo_admin"
DISCORD_ADMIN_PERMISSION = "discord_admin"


class GoosePermission(models.Model):
    USER_PERMISSION_CHOICES = [
        (
            BASIC_ACCESS,
            "Able to Apply to join and view the home page and other basic registered user pages",
        ),
        (LOOT_TRACKER, "Able to use the loot tracker"),
        (
            LOOT_TRACKER_ADMIN,
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
            SINGLE_CORP_ADMIN,
            "Able to approve corp applications for a specific corp and manage characters in that corp",
        ),
        (
            ALL_CORP_ADMIN,
            "Able to approve corp applications for all corps and manage characters in all corps",
        ),
        (SHIP_ORDERER, "Able to place ship orders"),
        (FREE_SHIP_ORDERER, "Able to place free ship orders"),
        (SHIP_ORDER_ADMIN, "Able to claim and work on ship orders"),
        (
            SHIP_PRICE_ADMIN,
            "Able to add/remove ship types and set if they are free or not",
        ),
        (
            VENMO_ADMIN,
            "Able to approve/deny pending venmo transactions.",
        ),
        (
            DISCORD_ADMIN_PERMISSION,
            "Able to change which discord server is connected to.",
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
                "description": f"A group which has all {settings.SITE_NAME} permissions.",
                "editable": True,
                "manually_given": True,
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


# Sorry...
# pylint: disable=too-many-public-methods
class GooseUser(models.Model):
    USER_STATUS_CHOICES = [
        ("unapproved", "unapproved"),
        ("approved", "approved"),
        ("rejected", "rejected"),
    ]
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
        choices=USER_STATUS_CHOICES,
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

    def give_manual_group(self, admin_making_change, new_group):
        if not admin_making_change:
            user = None
        else:
            user = admin_making_change.site_user
        Comment.objects.create(
            content_object=self,
            site=Site.objects.get_current(),
            user=user,
            comment=f"Gave Manual Group {new_group}",
            submit_date=timezone.now(),
        )
        self.give_group(new_group)

    def remove_manual_group(self, admin_making_change, new_group):
        Comment.objects.create(
            content_object=self,
            site=Site.objects.get_current(),
            user=admin_making_change.site_user,
            comment=f"Removed Manual Group {new_group}",
            submit_date=timezone.now(),
        )
        print(new_group)
        self.groupmember_set.filter(group=new_group).delete()

    def change_status(self, admin_making_change, new_status):
        if new_status != self.status:
            Comment.objects.create(
                content_object=self,
                site=Site.objects.get_current(),
                user=admin_making_change.site_user,
                comment=f"Changed status from {self.status} to {new_status}",
                submit_date=timezone.now(),
            )
            if new_status != "approved":
                for app in CorpApplication.objects.filter(character__user=self).all():
                    app.reject()
            self.status = new_status
            self.save()

    def groups(self):
        return self.groupmember_set.aggregate(
            groups=StringAgg(
                "group__name",
                delimiter=", ",
            )
        )["groups"]

    def has_perm(self, name_or_list: Union[str, List[str]]):
        if isinstance(name_or_list, str):
            perm_list = [name_or_list]
        else:
            perm_list = name_or_list
        # pylint: disable=no-member
        return (
            self.groupmember_set.filter(
                group__grouppermission__permission__name__in=perm_list
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
            return userapp_query.first()
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

    def can_apply_to_corp(self, corp):
        return corp in list(self.corps_user_can_apply_to())

    def corps_user_can_apply_to(self):
        # pylint: disable=no-member
        self.refresh_discord_data()  # type: ignore
        roles = self.extra_data().get("roles", [])
        return GooseUser.corps_roles_can_apply_to(roles)

    @staticmethod
    def corps_roles_can_apply_to(roles):
        corp_names = []
        for corp in Corp.objects.all():
            q = corp.discord_roles_allowing_application.filter(role_id__in=roles)
            if corp.public_corp or q.count() > 0:
                corp_names.append(corp.name)
        return Corp.objects.filter(name__in=corp_names)

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


class Character(models.Model):
    user = models.ForeignKey(GooseUser, on_delete=models.CASCADE)
    ingame_name = models.TextField(unique=True)
    corp = models.ForeignKey(Corp, on_delete=models.CASCADE)

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
    answers = models.JSONField(blank=True)  # type: ignore
    existing_character = models.ForeignKey(
        Character, on_delete=models.SET_NULL, null=True, blank=True
    )

    @staticmethod
    def unapproved_applications():
        return UserApplication.objects.filter(status="unapproved")

    def _create_character_application(self):
        if self.ingame_name:
            main_char = Character(
                user=self.user, ingame_name=self.ingame_name, corp=Corp.unknown_corp()
            )
            main_char.full_clean()
            main_char.save()
        else:
            main_char = self.existing_character  # type: ignore
        CorpApplication.new(
            status="unapproved",
            corp=self.corp,
            character=main_char,
        )

    def approve(self, approving_user=None):
        self.status = "approved"
        self.user.change_status(approving_user, "approved")
        self._create_character_application()
        self.full_clean()
        if self.corp.discord_role_given_on_approval:
            DiscordGuild.try_give_role(
                self.user.discord_uid(),
                self.corp.discord_role_given_on_approval.role_id,
            )
        if self.corp.manual_group_given_on_approval:
            self.user.give_manual_group(
                approving_user, self.corp.manual_group_given_on_approval
            )
        # pylint: disable=no-member
        self.user.refresh_discord_data()  # type: ignore
        self.save()

    def reject(self, rejecting_user):
        self.status = "rejected"
        self.user.change_status(rejecting_user, "rejected")
        self.full_clean()
        self.save()

    def __str__(self) -> str:
        return f"{self.status} User App for {self.user} made on {self.created_at}"


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

    @staticmethod
    def new(character, status, corp):
        app = CorpApplication.objects.create(
            character=character, status=status, corp=corp
        )
        if corp.auto_approve:
            app.approve(None)

    def approve(self, approving_user):
        self.status = "approved"
        self.character.corp = self.corp
        self.character.save()
        if self.corp.discord_role_given_on_approval:
            DiscordGuild.try_give_role(
                self.character.user.discord_uid(),
                self.corp.discord_role_given_on_approval.role_id,
            )
        if self.corp.manual_group_given_on_approval:
            self.character.user.give_manual_group(
                approving_user, self.corp.manual_group_given_on_approval
            )
        self.full_clean()
        self.save()

    def reject(self):
        self.status = "rejected"
        self.full_clean()
        self.save()

    @staticmethod
    def unapproved_applications():
        return CorpApplication.objects.filter(status="unapproved")
