from django.apps import AppConfig
from django.urls import reverse


def _format_url(url):
    return "".join(["http://", "localhost", ":8000", reverse(url)])


class StubDiscordAuthConfig(AppConfig):
    name = "stub_discord_auth"

    def ready(self):
        # pylint: disable=import-outside-toplevel

        # MonkeyPatch the discord oauth adapter so requests are sent to this app instead
        # allowing us to stub out discord entirely. We have to import instead ready
        # as allauth will crash if we attempt to import before Apps are loaded.
        from allauth.socialaccount.providers.discord.views import DiscordOAuth2Adapter

        DiscordOAuth2Adapter.access_token_url = _format_url("access_token_url")
        DiscordOAuth2Adapter.authorize_url = reverse("authorize_url")
        DiscordOAuth2Adapter.profile_url = _format_url("profile_url")
