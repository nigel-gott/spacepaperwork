from typing import Union

from django.contrib.auth.models import AbstractUser, Group
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from timezone_field import TimeZoneField


class Corp(models.Model):
    name = models.TextField(primary_key=True)

    def __str__(self):
        return str(self.name)


# Represents a unique single person using their unique discord uid if known. They might not have ever have visited goosetools and hence will not have a GooseUser model.
class DiscordUser(models.Model):
    username = models.TextField(unique=True)
    uid = models.TextField(unique=True, blank=True, null=True)
    avatar_hash = models.TextField(blank=True, null=True)

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


class GooseUser(AbstractUser):
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
    default_character = models.OneToOneField(Character, on_delete=models.CASCADE)

    def characters(self):
        if getattr(self, "discord_user"):
            return Character.objects.filter(discord_user=self.discord_user)
        else:
            return Character.objects.none()

    def discord_uid(self):
        return self.discord_user.uid

    def discord_username(self):
        return self.discord_user.username

    def discord_avatar_hash(self):
        return self.discord_user.uid


class DiscordGuild(models.Model):
    guild_id = models.TextField()
    bot_token = models.TextField()
    active = models.BooleanField(default=False)

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
