from django.apps import AppConfig
from django.urls import reverse


class StubDiscordAuthConfig(AppConfig):
    name = "stub_discord_auth"

    def ready(self):
        # MonkeyPatch the discord oauth adapter so requests are sent to this app instead allowing us to stub out discord entirely.
        from allauth.socialaccount.providers.discord.views import DiscordOAuth2Adapter

        DiscordOAuth2Adapter.access_token_url = self.get_url("access_token_url")
        DiscordOAuth2Adapter.authorize_url = self.get_url("authorize_url")
        DiscordOAuth2Adapter.profile_url = self.get_url("profile_url")

    def get_url(self, url):
        from django.contrib.sites.shortcuts import get_current_site

        return "".join(
            ["http://", get_current_site(None).domain, ":8000", reverse(url)]
        )
