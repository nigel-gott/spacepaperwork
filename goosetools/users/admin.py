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
)

admin.site.register(Corp)
admin.site.register(Character)
admin.site.register(DiscordUser)


class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        (
            None,
            {
                "fields": (
                    "timezone",
                    "transaction_tax",
                    "discord_user",
                    "default_character",
                    "broker_fee",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            None,
            {
                "fields": (
                    "timezone",
                    "transaction_tax",
                    "discord_user",
                    "default_character",
                    "broker_fee",
                )
            },
        ),
    )


admin.site.register(GooseUser, CustomUserAdmin)
admin.site.register(DiscordGuild)
admin.site.register(DiscordRoleDjangoGroupMapping)
