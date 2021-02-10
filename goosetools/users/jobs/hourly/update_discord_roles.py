import time

import requests
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django_extensions.management.jobs import HourlyJob
from django_tenants.utils import tenant_context
from requests.models import HTTPError

from goosetools.tenants.models import Client
from goosetools.users.discord_helpers import (
    merge,
    setup_user_groups_from_discord_guild_roles,
)
from goosetools.users.models import DiscordGuild, DiscordRole, GooseGroup, GooseUser


def refresh_from_discord():
    output = ""
    guild = DiscordGuild.objects.get(active=True)
    bot_headers = {
        "Authorization": "Bot {0}".format(settings.BOT_TOKEN),
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
                        + setup_user_groups_from_discord_guild_roles(
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
                                        required_discord_role__role_id=role_id
                                    ).name
                                )
                            except GooseGroup.DoesNotExist:
                                pass
                        if groups_they_should_have:
                            output = (
                                output
                                + f"WARNING: {user_json['user']['username']} has not registered in {settings.SITE_NAME} YET they have discord server roles for {','.join(groups_they_should_have)}.\n"
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
        output
        + f"======= APPROVED {settings.SITE_NAME} USERS WHO ARE NOT IN DISCORD ========\n"
    )
    for uid, user in uid_to_user.items():
        if user.status == "approved":
            characters = [str(c) for c in user.characters()]
            if user.groups():
                output = (
                    output
                    + f"{user.display_name()}({characters}) and has groups - {user.groups()}\n"
                )
            else:
                output = (
                    output + f"{user.display_name()}({characters}) and has no groups\n"
                )
    output = output + (f"Processed {users_processed} users.\n")
    return output


def refresh_from_discord_all():
    output = ""
    for tenant in Client.objects.all():
        with tenant_context(tenant):
            output = output + f"====== CLIENT {tenant.name} =========\n"
            DiscordRole.sync_from_discord()
            output = output + refresh_from_discord()
    return output


class Job(HourlyJob):
    help = "Checks discord roles and updates permissions accordingly"

    def execute(self):
        print(refresh_from_discord_all())
