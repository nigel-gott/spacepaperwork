import requests
from django.apps import AppConfig
from django.conf import settings


def _try_lookup_guild_roles(user_id):
    from goosetools.users.models import DiscordGuild

    try:
        guild = DiscordGuild.objects.get(active=True)
        if guild.guild_id:
            bot_headers = {
                "Authorization": "Bot {0}".format(settings.BOT_TOKEN),
                "Content-Type": "application/json",
            }
            discord_uid = user_id
            url = (
                f"https://discord.com/api/guilds/{guild.guild_id}/members/{discord_uid}"
            )
            return requests.get(url, headers=bot_headers).json()
    except DiscordGuild.DoesNotExist:
        pass
    return {}


class UsersConfig(AppConfig):
    name = "goosetools.users"
    verbose_name = "Users"

    def ready(self):
        from allauth.socialaccount.providers.discord.views import DiscordOAuth2Adapter
        from django_tenants.migration_executors.base import run_migrations
        from django_tenants.signals import schema_migrated

        from goosetools.users.handlers import handle_schema_migrated

        schema_migrated.connect(handle_schema_migrated, run_migrations)

        def complete_login_with_guild_roles(self, request, _app, token, **_kwargs):
            headers = {
                "Authorization": "Bearer {0}".format(token.token),
                "Content-Type": "application/json",
            }
            extra_data = requests.get(self.profile_url, headers=headers).json()
            if "id" in extra_data and request.tenant.name != "public":
                extra_data = {
                    **extra_data,
                    **_try_lookup_guild_roles(extra_data["id"]),
                }

            return self.get_provider().sociallogin_from_response(request, extra_data)

        DiscordOAuth2Adapter.complete_login = complete_login_with_guild_roles
