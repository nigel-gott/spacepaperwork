import requests
from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _try_lookup_guild_roles(user_id):
    from goosetools.users.models import DiscordGuild

    try:
        guild = DiscordGuild.objects.get(active=True)
        bot_headers = {
            "Authorization": "Bot {0}".format(guild.bot_token),
            "Content-Type": "application/json",
        }
        discord_uid = user_id
        url = f"https://discord.com/api/guilds/{guild.guild_id}/members/{discord_uid}"
        return requests.get(url, headers=bot_headers).json()
    except DiscordGuild.DoesNotExist:
        return {}


# pylint: disable=unused-argument
def populate_models(sender, **kwargs):
    from goosetools.users.models import AuthConfig, Corp, GoosePermission

    GoosePermission.ensure_populated()
    Corp.ensure_populated()
    AuthConfig.ensure_exists()


class IndustryConfig(AppConfig):
    name = "goosetools.industry"


class UsersConfig(AppConfig):
    name = "goosetools.users"
    verbose_name = "Users"

    def ready(self):
        from allauth.socialaccount.providers.discord.views import DiscordOAuth2Adapter

        post_migrate.connect(populate_models, sender=self)

        def complete_login_with_guild_roles(self, request, _app, token, **_kwargs):
            headers = {
                "Authorization": "Bearer {0}".format(token.token),
                "Content-Type": "application/json",
            }
            extra_data = requests.get(self.profile_url, headers=headers).json()
            if "id" in extra_data:
                extra_data = {
                    **extra_data,
                    **_try_lookup_guild_roles(extra_data["id"]),
                }

            return self.get_provider().sociallogin_from_response(request, extra_data)

        DiscordOAuth2Adapter.complete_login = complete_login_with_guild_roles
