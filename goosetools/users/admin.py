# mypy: ignore-errors
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from goosetools.users.models import (
    Character,
    Corp,
    CorpApplication,
    DiscordGuild,
    DiscordRoleDjangoGroupMapping,
    DiscordUser,
    GooseUser,
    UserApplication,
)


class CharacterAdmin(admin.ModelAdmin):
    search_fields = ["ingame_name"]
    list_display = [
        "ingame_name",
        "corp",
        "discord_nickname",
        "discord_username",
        "status",
    ]
    list_filter = ["corp"]

    # pylint: disable=no-self-use
    def discord_username(self, obj):
        return obj.discord_user.username

    # pylint: disable=no-self-use
    def discord_nickname(self, obj):
        return obj.discord_user.nick

    # pylint: disable=no-self-use
    def status(self, obj):
        return obj.discord_user.gooseuser.status


class CustomDiscordUserAdmin(admin.ModelAdmin):
    search_fields = ["username"]
    list_display = [
        "username",
        "nick",
        "uid",
        "pre_approved",
        "old_notes",
        "sa_profile",
        "voucher",
    ]


admin.site.register(Corp)
admin.site.register(Character, CharacterAdmin)
admin.site.register(DiscordUser, CustomDiscordUserAdmin)
admin.site.register(UserApplication)
admin.site.register(CorpApplication)


class CustomUserAdmin(UserAdmin):
    list_display = [
        "discord_nickname",
        "discord_username",
        "characters",
        "groups_list",
        "status",
        "is_staff",
        "notes_with_old",
        "sa_profile",
        "vouched_by",
        "vouches",
    ]

    # pylint: disable=no-self-use
    def discord_username(self, obj):
        return obj.discord_user.username

    # pylint: disable=no-self-use
    def discord_nickname(self, obj):
        return obj.discord_user.nick

    # pylint: disable=no-self-use
    def characters(self, obj):
        return [str(char) for char in obj.characters()]

    # pylint: disable=no-self-use
    def groups_list(self, obj):
        return [str(group) for group in obj.groups.all()]

    def notes_with_old(self, obj):
        if obj.discord_user.old_notes:
            return str(obj.notes) + "\n OLD NOTES: " + str(obj.discord_user.old_notes)
        else:
            return obj.notes

    def sa_profile(self, obj):
        return obj.discord_user.sa_profile

    def vouched_by(self, obj):
        return obj.discord_user.voucher

    def vouches(self, obj):
        return [str(v.display_name()) for v in obj.discord_user.current_vouches.all()]

    fieldsets = UserAdmin.fieldsets + (
        (
            None,
            {
                "fields": (
                    "transaction_tax",
                    "discord_user",
                    "default_character",
                    "broker_fee",
                    "status",
                    "notes",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            None,
            {
                "fields": (
                    "transaction_tax",
                    "discord_user",
                    "default_character",
                    "broker_fee",
                    "status",
                    "notes",
                )
            },
        ),
    )


admin.site.register(GooseUser, CustomUserAdmin)
admin.site.register(DiscordGuild)
admin.site.register(DiscordRoleDjangoGroupMapping)
