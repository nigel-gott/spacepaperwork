import logging

import requests
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from timezone_field import TimeZoneField

logger = logging.getLogger(__name__)


class Corp(models.Model):
    name = models.TextField(primary_key=True)
    full_name = models.TextField(unique=True, null=True, blank=True)
    required_discord_role = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.name)


# Represents a unique single person using their unique discord uid if known. They might not have ever have visited goosetools and hence will not have a GooseUser model.
class DiscordUser(models.Model):
    username = models.TextField(unique=True)
    nick = models.TextField(null=True, blank=True)
    uid = models.TextField(unique=True, blank=True, null=True)

    def display_name(self):
        if self.nick:
            return self.nick
        else:
            return self.username

    def __str__(self):
        return self.username


@deconstructible
class UnicodeAndSpacesUsernameValidator(UnicodeUsernameValidator):
    regex = r"^[-\w.@+ ]+\Z"
    message = _(
        "Enter a valid username. This value may contain only letters, "
        "numbers, and @/./+/-/_/space  characters."
    )
    flags = 0


class GooseUser(ExportModelOperationsMixin("gooseuser"), AbstractUser):  # type: ignore
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[],
        error_messages={"unique": _("A user with that username already exists.")},
    )

    discord_user = models.OneToOneField(
        DiscordUser, on_delete=models.CASCADE, null=True, blank=True
    )
    timezone = TimeZoneField(default="Europe/London")
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
    notes = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)  # type: ignore
    sa_profile = models.TextField(blank=True, null=True)
    voucher = models.ForeignKey(
        "GooseUser",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="current_vouches",
    )

    def latest_app(self):
        if hasattr(self, "userapplication"):
            # pylint: disable=no-member
            return self.userapplication
        else:
            return False

    def is_approved(self):
        return self.status == "approved"

    def is_unapproved(self):
        return self.status == "unapproved"

    def is_rejected(self):
        return self.status == "rejected"

    def is_authed_and_approved(self):
        return self.is_authenticated and self.is_approved()

    def set_as_approved(self):
        self.status = "approved"
        self.save()

    def set_as_rejected(self):
        self.status = "rejected"
        self.save()

    def characters(self):
        return self.character_set.all()

    def _discord_account(self):
        return self.socialaccount_set.get(provider="discord")

    def discord_uid(self):
        return self._discord_account().uid

    def discord_username(self):
        username = self._extra_data().get("username")
        discriminator = self._extra_data().get("discriminator")
        return "{}#{}".format(username, discriminator)

    def display_name(self):
        if "nick" in self._extra_data():
            nick = self._extra_data()["nick"]
            if nick and nick.strip():
                return nick.strip()
        return self.discord_username()

    def discord_avatar_url(self):
        return self._construct_avatar_url()

    def _extra_data(self):
        return self._discord_account().extra_data

    def _discord_discriminator(self):
        return self._extra_data()["discriminator"]

    def _avatar_hash(self):
        return "avatar" in self._extra_data() and self._extra_data()["avatar"]

    # default avatars look like this: https://cdn.discordapp.com/embed/avatars/3.png
    # there is a bug with discord's size selecting mechanism for these, doing 3.png?size=16 still returns a full size default avatar.
    def _has_default_avatar(self):
        return not self._avatar_hash() or len(str(self._avatar_hash())) == 1

    def _construct_avatar_url(self):
        if self._has_default_avatar():
            avatar_number = int(self._discord_discriminator()) % 5
            return f"https://cdn.discordapp.com/embed/avatars/{avatar_number}.png"
        return f"https://cdn.discordapp.com/avatars/{self.discord_uid()}/{self._avatar_hash()}.png"


class UserApplication(models.Model):
    user = models.OneToOneField(GooseUser, on_delete=models.CASCADE)
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
    ingame_name = models.TextField()
    corp = models.ForeignKey(Corp, on_delete=models.CASCADE)

    previous_alliances = models.TextField(blank=True, null=True)
    activity = models.TextField(blank=True, null=True)
    looking_for = models.TextField(blank=True, null=True)

    @staticmethod
    def unapproved_applications():
        return UserApplication.objects.filter(status="unapproved")

    def _create_character(self):
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


class DiscordRoleDjangoGroupMapping(models.Model):
    guild = models.ForeignKey(DiscordGuild, on_delete=models.CASCADE)
    role_id = models.TextField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    grants_staff = models.BooleanField(default=False)


class Character(models.Model):
    discord_user = models.ForeignKey(
        DiscordUser, on_delete=models.CASCADE, null=True, blank=True
    )
    user = models.ForeignKey(GooseUser, on_delete=models.CASCADE, null=True, blank=True)
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
