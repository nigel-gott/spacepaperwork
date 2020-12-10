# mypy: ignore-errors
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from goosetools.users.models import (
    Character,
    Corp,
    DiscordGuild,
    DiscordRoleDjangoGroupMapping,
    DiscordUser,
    GooseUser,
    UserApplication,
)

admin.site.register(Corp)
admin.site.register(Character)
admin.site.register(DiscordUser)
admin.site.register(UserApplication)


class CustomUserAdmin(UserAdmin):

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
