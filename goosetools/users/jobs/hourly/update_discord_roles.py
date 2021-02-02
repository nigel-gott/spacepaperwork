import time
from typing import Any, Dict

import requests
from allauth.socialaccount.models import SocialAccount
from django_extensions.management.jobs import HourlyJob
from requests.models import HTTPError

from goosetools.tenants.models import SiteUser
from goosetools.users.models import (
    DiscordGuild,
    DiscordRoleDjangoGroupMapping,
    GooseGroup,
    GooseUser,
)


def _setup_user_groups_from_discord_guild_roles(
    siteuser: SiteUser,
    extra_data: Dict[str, Any],
    guild: DiscordGuild,
    log_output=False,
):
    try:
        siteuser.groups.clear()
        if not siteuser.is_superuser:
            siteuser.is_staff = False
        if siteuser.has_gooseuser():
            siteuser.gooseuser.groupmember_set.all().delete()
        if "roles" in extra_data:
            for role_id in extra_data["roles"]:
                if siteuser.has_gooseuser():
                    _setup_new_permissions(role_id, siteuser.gooseuser, log_output)
                _setup_old_permissions(role_id, guild, siteuser, log_output)
            siteuser.save()
    except DiscordGuild.DoesNotExist:
        pass


def _setup_new_permissions(role_id: str, gooseuser: GooseUser, log_output: bool):
    groups = GooseGroup.objects.filter(linked_discord_role__discord_role_uid=role_id)
    for group in groups.all():
        if log_output:
            print(f"New: Giving {group.name} to {gooseuser}")
        gooseuser.give_group(group)


def _setup_old_permissions(
    role_id: str, guild: DiscordGuild, siteuser: SiteUser, log_output: bool
):
    try:
        group_mappings = DiscordRoleDjangoGroupMapping.objects.filter(
            role_id=role_id, guild=guild
        )
        for group_mapping in group_mappings.all():
            if log_output:
                print(f"Giving {group_mapping.group} to {siteuser}")
            siteuser.groups.add(group_mapping.group)
            if group_mapping.grants_staff:
                if log_output:
                    print(
                        f"Granting staff to {siteuser} as they have group {group_mapping.group}"
                    )
                siteuser.is_staff = True
    except DiscordRoleDjangoGroupMapping.DoesNotExist:
        pass


class Job(HourlyJob):
    help = "Checks discord roles and updates goosetools permissions accordingly"

    def execute(self):
        guild = DiscordGuild.objects.get(active=True)
        bot_headers = {
            "Authorization": "Bot {0}".format(guild.bot_token),
            "Content-Type": "application/json",
        }

        highest_id_so_far = 0
        previous_highest_id = -1
        users_processed = 0
        try:
            while previous_highest_id < highest_id_so_far:
                previous_highest_id = highest_id_so_far
                url = f"https://discord.com/api/guilds/{guild.guild_id}/members?limit=1000"
                if highest_id_so_far > 0:
                    url = url + "&after=" + str(highest_id_so_far)

                members_request = requests.get(url, headers=bot_headers)
                members_request.raise_for_status()
                users_json = members_request.json()
                for user_json in users_json:
                    time.sleep(1)
                    uid = user_json["user"]["id"]
                    if int(uid) > highest_id_so_far:
                        highest_id_so_far = int(uid)
                    try:
                        existing_socialaccount = SocialAccount.objects.get(uid=uid)
                        _setup_user_groups_from_discord_guild_roles(
                            existing_socialaccount.user,
                            user_json,
                            guild,
                            log_output=True,
                        )
                    except SocialAccount.DoesNotExist:
                        print(
                            f"Not doing anything for {user_json['user']['username']} as they are not in goosetools."
                        )
                    users_processed = users_processed + 1
                time.sleep(10)
        except HTTPError as e:
            print(
                "Got to "
                + str(highest_id_so_far)
                + " before discord stopped returning more users: "
                + str(e)
            )
        print(f"Processed {users_processed} users.")
