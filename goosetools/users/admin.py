# mypy: ignore-errors
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

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


admin.site.register(Corp)
admin.site.register(Character, CharacterAdmin)
admin.site.register(DiscordUser)
admin.site.register(UserApplication)
admin.site.register(CorpApplication)


class CustomUserAdmin(UserAdmin):
    list_display = [
        "discord_username",
        "discord_nickname",
        "characters",
        "groups_list",
        "status",
        "is_staff",
        "notes",
        "sa_profile",
        "voucher",
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

    def vouches(self, obj):
        return [str(v.display_name()) for v in obj.current_vouches.all()]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        form.base_fields["username"].disabled = True

        return form

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "status",
                    "notes",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": ("is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "status",
                    "notes",
                )
            },
        ),
    )


admin.site.register(GooseUser, CustomUserAdmin)
admin.site.register(DiscordGuild)
admin.site.register(DiscordRoleDjangoGroupMapping)
