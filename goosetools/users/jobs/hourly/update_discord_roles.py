import time
from typing import Any, Dict

import requests
from allauth.socialaccount.models import SocialAccount
from django_extensions.management.jobs import HourlyJob
from requests.models import HTTPError

from goosetools.tenants.models import SiteUser
from goosetools.users.models import DiscordGuild, GooseGroup, GooseUser


def _setup_user_groups_from_discord_guild_roles(
    siteuser: SiteUser,
    extra_data: Dict[str, Any],
):
    output = ""
    siteuser.groups.clear()
    if not siteuser.is_superuser:
        siteuser.is_staff = False
    else:
        output = output + " - Gave Superuser\n"

    if siteuser.has_gooseuser():
        siteuser.gooseuser.groupmember_set.all().delete()
        if siteuser.is_superuser:
            superuser_group = GooseGroup.superuser_group()
            siteuser.gooseuser.give_group(superuser_group)
        if "roles" in extra_data:
            for role_id in extra_data["roles"]:
                output = output + _setup_new_permissions(role_id, siteuser.gooseuser)
        siteuser.save()
    return f"Syncing {siteuser.username}\n" + output


def _setup_new_permissions(role_id: str, gooseuser: GooseUser):
    groups = GooseGroup.objects.filter(linked_discord_role=role_id)
    output = ""
    for group in groups.all():
        output = output + (f" - Gave {group.name} to {gooseuser}\n")
        gooseuser.give_group(group)
    return output


def refresh_from_discord():
    guild = DiscordGuild.objects.get(active=True)
    output = ""
    bot_headers = {
        "Authorization": "Bot {0}".format(guild.bot_token),
        "Content-Type": "application/json",
    }

    highest_id_so_far = 0
    previous_highest_id = -1
    all_users = GooseUser.objects.all()
    uid_to_user = {u.discord_uid(): u for u in all_users}
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
                uid = user_json["user"]["id"]
                uid_to_user.pop(uid, None)
                if int(uid) > highest_id_so_far:
                    highest_id_so_far = int(uid)
                try:
                    existing_socialaccount = SocialAccount.objects.get(uid=uid)
                    output = (
                        output
                        + _setup_user_groups_from_discord_guild_roles(
                            existing_socialaccount.user,
                            user_json,
                        )
                        + "\n"
                    )
                    merge(existing_socialaccount.extra_data, user_json)
                    existing_socialaccount.save()
                    if existing_socialaccount.user.has_gooseuser():
                        existing_socialaccount.user.gooseuser.cache_fields_from_social_account()
                except SocialAccount.DoesNotExist:
                    if "roles" in users_json:
                        groups_they_should_have = []
                        for role_id in users_json["roles"]:
                            try:
                                groups_they_should_have.append(
                                    GooseGroup.objects.get(
                                        linked_discord_role=role_id
                                    ).name
                                )
                            except GooseGroup.DoesNotExist:
                                pass
                        if groups_they_should_have:
                            output = (
                                output
                                + f"WARNING: {user_json['user']['username']} has not registered in goosetools YET they have discord server roles for {','.join(groups_they_should_have)}.\n"
                            )
                users_processed = users_processed + 1
            time.sleep(10)
    except HTTPError as e:
        output = output + (
            "Got to "
            + str(highest_id_so_far)
            + " before discord stopped returning more users: "
            + str(e)
            + "\n"
        )

    output = (
        output + "======= APPROVED GOOSETOOLS USERS WHO ARE NOT IN DISCORD ========\n"
    )
    for uid, user in uid_to_user.items():
        if user.status == "approved":
            characters = [str(c) for c in user.characters()]
            if user.groups():
                output = (
                    output
                    + f"{user.display_name()}({characters}) and has goosetools groups - {user.groups()}\n"
                )
            else:
                output = (
                    output
                    + f"{user.display_name()}({characters}) and has no goosetools groups\n"
                )
    output = output + (f"Processed {users_processed} users.\n")
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


# adding ships
# changing the free ship groups
# seeing characters / removing / editing
# add user notes


class Job(HourlyJob):
    help = "Checks discord roles and updates goosetools permissions accordingly"

    def execute(self):
        print(refresh_from_discord())
