# mypy: ignore-errors
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.contrib.auth.admin import UserAdmin

from config.middleware import SiteUser
from goosetools.users.models import (
    AuthConfig,
    Character,
    Corp,
    CorpApplication,
    CrudAccessController,
    DiscordGuild,
    GooseGroup,
    GoosePermission,
    GooseUser,
    GroupMember,
    GroupPermission,
    PermissibleEntity,
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
admin.site.register(AuthConfig)
admin.site.register(GoosePermission)
admin.site.register(GooseGroup)
admin.site.register(GroupMember)
admin.site.register(GroupPermission)
admin.site.register(CrudAccessController)
admin.site.register(PermissibleEntity)


class CustomUserAdmin(ModelAdmin):
    fields = ("site_user", "status", "notes", "sa_profile", "voucher")
    readonly_fields = ("site_user", "voucher")
    search_fields = ["site_user__username"]
    list_filter = ["status"]
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

    # pylint: disable=no-self-use
    def vouches(self, obj):
        return [str(v.display_name()) for v in obj.current_vouches.all()]


class CustomSiteUserAdmin(UserAdmin):
    search_fields = ["username"]


admin.site.register(GooseUser, CustomUserAdmin)
admin.site.register(DiscordGuild)
admin.site.register(SiteUser, CustomSiteUserAdmin)
