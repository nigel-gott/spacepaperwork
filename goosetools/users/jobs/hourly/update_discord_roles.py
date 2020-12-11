import requests
from django_extensions.management.jobs import HourlyJob
from requests.models import HTTPError

from goosetools.users.models import (
    DiscordGuild,
    DiscordRoleDjangoGroupMapping,
    GooseUser,
)


def _setup_user_groups_from_discord_guild_roles(
    user, extra_data, guild, log_output=False
):
    try:
        user.groups.clear()
        if not user.is_superuser:
            user.is_staff = False
        if "nick" in extra_data and extra_data["nick"] and extra_data["nick"].strip():
            user.discord_user.nick = extra_data["nick"]
            user.discord_user.save()
        if guild.member_role_id:
            has_member_role = False
        else:
            has_member_role = True
        if "roles" in extra_data:
            for role_id in extra_data["roles"]:
                if guild.member_role_id == role_id:
                    has_member_role = True
                    if log_output:
                        DiscordGuild.try_give_role(user, "750897450365222962")
                try:
                    group_mappings = DiscordRoleDjangoGroupMapping.objects.filter(
                        role_id=role_id, guild=guild
                    )
                    for group_mapping in group_mappings.all():
                        if log_output:
                            print(f"Giving {group_mapping.group} to {user}")
                        user.groups.add(group_mapping.group)
                        if group_mapping.grants_staff:
                            if log_output:
                                print(
                                    f"Granting staff to {user} as they have group {group_mapping.group}"
                                )
                            user.is_staff = True
                except DiscordRoleDjangoGroupMapping.DoesNotExist:
                    pass
        if not has_member_role:
            if log_output:
                print(
                    f"Marking {user} as rejected as they do not have the role {guild.member_role_id}"
                )
            user.rejected()
    except DiscordGuild.DoesNotExist:
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
        try:
            while previous_highest_id < highest_id_so_far:
                previous_highest_id = highest_id_so_far
                url = f"https://discord.com/api/guilds/{guild.guild_id}/members?limit=1000"
                if highest_id_so_far > 0:
                    url = url + "&after=" + str(highest_id_so_far)

                members_request = requests.get(url, headers=bot_headers)
                members_request.raise_for_status()
                users = members_request.json()
                for user in users:
                    uid = user["user"]["id"]
                    if int(uid) > highest_id_so_far:
                        highest_id_so_far = int(uid)
                    try:
                        gooseuser = GooseUser.objects.get(discord_user__uid=uid)
                        _setup_user_groups_from_discord_guild_roles(
                            gooseuser, user, guild, log_output=True
                        )
                    except GooseUser.DoesNotExist:
                        print(
                            f"Not doing anything for {user['user']['username']} as they are not in goosetools."
                        )
        except HTTPError:
            print(
                "Got to "
                + str(highest_id_so_far)
                + " before discord stopped returning more users."
            )
