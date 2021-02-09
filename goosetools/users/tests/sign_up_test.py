import requests_mock
from django.urls.base import reverse
from freezegun import freeze_time

from goosetools.tests.goosetools_test_case import GooseToolsTestCase
from goosetools.users.models import AuthConfig, DiscordGuild


def mock_discord_returns_with_uid(
    m, uid, roles=None, profile_username="TEST USER", profile_discriminator="1234"
):
    m.post(
        "http://localhost:8000/stub_discord_auth/access_token_url",
        json={"access_token": "stub_access_code"},
        headers={"content-type": "application/json"},
    )
    profile_json = {
        "id": uid,
        "username": profile_username,
        "avatar": "e71b856158d285d6ac6e8877d17bae45",
        "discriminator": profile_discriminator,
        "public_flags": 0,
        "flags": 0,
        "locale": "en-US",
        "mfa_enabled": True,
    }
    if roles is not None:
        profile_json["roles"] = roles
    m.get(
        "http://localhost:8000/stub_discord_auth/profile_url",
        json=profile_json,
        headers={"content-type": "application/json"},
    )


@freeze_time("2012-01-14 12:00:00")
class UserAuthTest(GooseToolsTestCase):
    fixtures = ["goosetools/users/fixtures/test/test.json"]

    def test_when_signup_required_and_conduct_set_splash_page_links_to_conduct_first(
        self,
    ):
        AuthConfig.objects.create(active=True, code_of_conduct="CUSTOM CODE OF CONDUCT")
        with requests_mock.Mocker() as m:
            mock_discord_returns_with_uid(m, "3")
            self.client.logout()
            response = self.client.get(reverse("core:splash"), follow=True)
            self.assertIn(
                f'<a id="conduct_button" class="btn waves-btn green btn-large pulse" href="{reverse("core:conduct")}">HONK</a>',
                str(response.content, encoding="utf-8"),
            )
            conduct = self.client.get(reverse("core:conduct"), follow=True)
            self.assertIn(
                "CUSTOM CODE OF CONDUCT",
                str(conduct.content, encoding="utf-8"),
            )

    def test_a_user_with_user_admin_perm_can_change_code_of_conduct(
        self,
    ):
        DiscordGuild.objects.create(active=True, guild_id="old")
        AuthConfig.objects.create(active=True, code_of_conduct="CUSTOM CODE OF CONDUCT")
        self.user.give_group(self.user_admin_group)
        with requests_mock.Mocker() as m:
            m.get(
                "https://discord.com/api/guilds/id/members/3",
                json={},
                headers={"content-type": "application/json"},
            )
            self.post(
                reverse("auth_settings"),
                {"code_of_conduct": "NEW DIFFERENT CODE", "discord_guild_id": "id"},
            )
            mock_discord_returns_with_uid(m, "3")
            self.client.logout()
            self.client.get(reverse("core:splash"), follow=True)
            conduct = self.client.get(reverse("core:conduct"))
            self.assertIn(
                "NEW DIFFERENT CODE",
                str(conduct.content, encoding="utf-8"),
            )
            self.assertEqual(DiscordGuild.objects.get(active=True).guild_id, "id")

    def test_a_user_with_no_perms_cant_change_code_of_conduct(
        self,
    ):
        AuthConfig.objects.create(active=True, code_of_conduct="CUSTOM CODE OF CONDUCT")
        should_be_forbidden = self.client.post(
            reverse("auth_settings"), {"code_of_conduct": "NEW DIFFERENT CODE"}
        )
        self.assertEqual(should_be_forbidden.status_code, 403)
