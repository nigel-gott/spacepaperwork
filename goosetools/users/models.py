from typing import Union

import requests
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from timezone_field import TimeZoneField


class Corp(models.Model):
    name = models.TextField(primary_key=True)
    required_discord_role = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.name)


# Represents a unique single person using their unique discord uid if known. They might not have ever have visited goosetools and hence will not have a GooseUser model.
class DiscordUser(models.Model):
    username = models.TextField(unique=True)
    nick = models.TextField(null=True, blank=True)
    uid = models.TextField(unique=True, blank=True, null=True)
    avatar_hash = models.TextField(blank=True, null=True)

    pre_approved = models.BooleanField(default=False)

    def display_name(self):
        if self.nick:
            return self.nick
        else:
            return self.username

    def avatar_url(self) -> Union[bool, str]:
        return self._construct_avatar_url()

    # default avatars look like this: https://cdn.discordapp.com/embed/avatars/3.png
    # there is a bug with discord's size selecting mechanism for these, doing 3.png?size=16 still returns a full size default avatar.
    def has_default_avatar(self):
        return not self.avatar_hash or len(str(self.avatar_hash)) == 1

    def has_custom_avatar(self):
        return self.avatar_hash and self.uid and not self.has_default_avatar()

    def _construct_avatar_url(self):
        if self.has_default_avatar():
            if "#" in self.username:
                # TODO add discriminator as a real non null field on DiscordUser and just access it here.
                avatar_number = int(self.username.split("#")[1]) % 5
            else:
                avatar_number = 1
            return f"https://cdn.discordapp.com/embed/avatars/{avatar_number}.png"
        return f"https://cdn.discordapp.com/avatars/{self.uid}/{self.avatar_hash}.png"

    def __str__(self):
        return self.username


class Character(models.Model):
    discord_user = models.ForeignKey(DiscordUser, on_delete=models.CASCADE)
    ingame_name = models.TextField(unique=True)
    corp = models.ForeignKey(Corp, on_delete=models.CASCADE)

    # pylint: disable=no-member
    def gooseuser_or_false(self):
        return (
            self.discord_user
            and hasattr(self.discord_user, "gooseuser")
            and self.discord_user.gooseuser
        )

    def discord_avatar_url(self):
        return self.discord_user and self.discord_user.avatar_url()

    def discord_username(self):
        return self.discord_user and self.discord_user.username

    def display_name(self):
        return self.discord_user and self.discord_user.display_name()

    def __str__(self):
        return f"[{self.corp}] {self.ingame_name}"


# Add nullable discord_user FK to Character/GooseUser
# Add new Discord User Model
# Copy over character data into discord user model
# Remove nullability and old fields from models + update code


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
        validators=[UnicodeAndSpacesUsernameValidator()],
        error_messages={"unique": _("A user with that username already exists.")},
    )

    discord_user = models.OneToOneField(DiscordUser, on_delete=models.CASCADE)
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
        Character, on_delete=models.CASCADE, null=True, blank=True
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

    def is_approved(self):
        return self.status == "approved"

    def is_authed_and_approved(self):
        return self.is_authenticated and self.is_approved()

    def approved(self):
        self.status = "approved"
        self.save()

    def rejected(self):
        self.status = "rejected"
        self.save()

    def characters(self):
        if getattr(self, "discord_user"):
            return Character.objects.filter(discord_user=self.discord_user)
        else:
            return Character.objects.none()

    def discord_uid(self):
        return self.discord_user.uid

    def discord_username(self):
        return self.discord_user.username

    def display_name(self):
        return self.discord_user.display_name()

    def discord_avatar_hash(self):
        return self.discord_user.uid

    def discord_avatar_url(self):
        return self.discord_user.avatar_url()


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

    @staticmethod
    def unapproved_applications():
        return UserApplication.objects.filter(status="unapproved")

    def _create_character(self):
        main_char = Character(
            discord_user=self.user.discord_user,
            ingame_name=self.ingame_name,
            corp=self.corp,
        )
        main_char.full_clean()
        main_char.save()

    def approve(self):
        self.status = "approved"
        self.user.approved()
        self._create_character()
        self.full_clean()
        DiscordGuild.try_give_guild_member_role(self.user)
        self.save()

    def reject(self):
        self.status = "rejected"
        self.user.rejected()
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
            DiscordGuild.try_give_role(user.discord_uid(), guild.member_role_id)
        except DiscordGuild.DoesNotExist:
            pass

    @staticmethod
    def try_give_role(uid, role_id):
        try:
            guild = DiscordGuild.objects.get(active=True)
            if guild.member_role_id:
                bot_headers = {
                    "Authorization": "Bot {0}".format(guild.bot_token),
                }
                url = f"https://discord.com/api/guilds/{guild.guild_id}/members/{uid}/roles/{role_id}"
                request = requests.put(url, headers=bot_headers)
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
