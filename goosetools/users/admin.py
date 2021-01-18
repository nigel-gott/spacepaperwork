# mypy: ignore-errors
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin

from goosetools.users.models import (
    Character,
    Corp,
    CorpApplication,
    DiscordGuild,
    DiscordRoleDjangoGroupMapping,
    GooseUser,
    UserApplication,
)


class CharacterAdmin(admin.ModelAdmin):
    search_fields = ["ingame_name"]
    list_display = [
        "ingame_name",
        "corp",
        "discord_username",
        "display_name",
        "status",
    ]
    list_filter = ["corp"]

    # pylint: disable=no-self-use
    def discord_username(self, obj):
        return obj.user.discord_username()

    # pylint: disable=no-self-use
    def display_name(self, obj):
        return obj.user.display_name()

    # pylint: disable=no-self-use
    def status(self, obj):
        return obj.user.status


admin.site.register(Corp)
admin.site.register(Character, CharacterAdmin)
admin.site.register(UserApplication)
admin.site.register(CorpApplication)


class CustomUserAdmin(ModelAdmin):
    list_display = [
        "username",
        "display_name",
        "characters",
        "status",
        "notes",
        "sa_profile",
        "voucher",
        "vouches",
    ]

    # pylint: disable=no-self-use
    def username(self, obj):
        return obj.site_user.username

    # pylint: disable=no-self-use
    def characters(self, obj):
        return [str(char) for char in obj.characters()]

    def vouches(self, obj):
        return [str(v.display_name()) for v in obj.current_vouches.all()]


admin.site.register(GooseUser, CustomUserAdmin)
admin.site.register(DiscordGuild)
admin.site.register(DiscordRoleDjangoGroupMapping)
