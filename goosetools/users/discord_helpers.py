from typing import Any, Dict

import requests
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from requests.exceptions import HTTPError

from goosetools.tenants.models import SiteUser
from goosetools.users.models import DiscordGuild, GooseGroup, GooseUser


def refresh_discord_data(self):
    try:
        guild = DiscordGuild.objects.get(active=True)
        bot_headers = {
            "Authorization": "Bot {0}".format(settings.BOT_TOKEN),
        }
        uid = self.discord_uid()
        url = f"https://discord.com/api/guilds/{guild.guild_id}/members/{uid}"
        try:
            request = requests.get(url, headers=bot_headers)
            request.raise_for_status()
        except HTTPError as e:
            return f"Unknown error syncing {self}. Discord config might be incorrect or they might no longer be on the server: {e}"
        existing_socialaccount = SocialAccount.objects.get(uid=uid)
        merge(existing_socialaccount.extra_data, request.json())
        existing_socialaccount.save()
        self.cache_fields_from_social_account()
        return setup_user_groups_from_discord_guild_roles(
            existing_socialaccount.user,
            existing_socialaccount.extra_data,
        )

    except DiscordGuild.DoesNotExist:
        pass


GooseUser.refresh_discord_data = refresh_discord_data  # type: ignore


def setup_user_groups_from_discord_guild_roles(
    siteuser: SiteUser,
    extra_data: Dict[str, Any],
):
    output = ""

    if siteuser.has_gooseuser():
        siteuser.gooseuser.groupmember_set.exclude(group__manually_given=True).delete()
        if siteuser.is_superuser:
            superuser_group = GooseGroup.superuser_group()
            siteuser.gooseuser.give_group(superuser_group)
        if "roles" in extra_data:
            for role_id in extra_data["roles"]:
                output = output + _setup_new_permissions(role_id, siteuser.gooseuser)
        siteuser.save()
    return f"Synced {siteuser.username}\n" + output


def _setup_new_permissions(role_id: str, gooseuser: GooseUser):
    groups = GooseGroup.objects.filter(required_discord_role__role_id=role_id)
    output = ""
    for group in groups.all():
        output = output + (f" - Gave {group.name} to {gooseuser}\n")
        gooseuser.give_group(group)
    return output


def merge(a, b, path=None):
    "merges b into a"
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a
