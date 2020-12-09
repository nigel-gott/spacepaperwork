import requests_mock
from django.urls.base import reverse
from freezegun import freeze_time

from goosetools.tests.goosetools_test_case import GooseToolsTestCase
from goosetools.users.models import DiscordUser


@freeze_time("2012-01-14 12:00:00")
class UserAuthTest(GooseToolsTestCase):
    fixtures = ["goosetools/users/fixtures/test/test.json"]

    def test_approved_user_can_see_non_whitelisted_page(self):
        response = self.client.get(reverse("fleet"))
        self.assertIn("Active Fleets", str(response.content, encoding="utf-8"))
        self.assert_messages(response, [])

    def test_unapproved_user_cant_see_non_whitelisted_page(self):
        self.user.status = "unapproved"
        self.user.save()

        response = self.client.get(reverse("fleet"))
        self.assertNotIn("Active Fleets", str(response.content, encoding="utf-8"))
        self.assertRedirects(response, "/goosetools/")
        self.assert_messages(
            response,
            [("error", "You are not yet approved and cannot access this page.")],
        )

    def test_a_preapproved_discord_user_is_approved_after_signing_up(self):
        with requests_mock.Mocker() as m:
            m.post(
                "http://localhost:8000/goosetools/stub_discord_auth/access_token_url",
                json={"access_token": "stub_access_code"},
                headers={"content-type": "application/json"},
            )
            m.get(
                "http://localhost:8000/goosetools/stub_discord_auth/profile_url",
                json={
                    "id": "3",
                    "username": "TEST USER",
                    "avatar": "e71b856158d285d6ac6e8877d17bae45",
                    "discriminator": "1234",
                    "public_flags": 0,
                    "flags": 0,
                    "locale": "en-US",
                    "mfa_enabled": True,
                },
                headers={"content-type": "application/json"},
            )
            DiscordUser.objects.create(
                username="Preapproved Discord User", uid="3", pre_approved=True
            )
            self.client.logout()
            response = self.client.get("/goosetools/", follow=True)
            last_url, _ = response.redirect_chain[-1]
            self.post(
                last_url,
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "broker_fee": 3,
                    "username": "test",
                },
            )
            response = self.client.get(reverse("fleet"))
            self.assert_messages(
                response, [("success", "Successfully signed in as test.")]
            )
            self.assertIn("Active Fleets", str(response.content, encoding="utf-8"))

    def test_an_unknown_discord_user_is_unapproved_after_signing_up(self):
        with requests_mock.Mocker() as m:
            m.post(
                "http://localhost:8000/goosetools/stub_discord_auth/access_token_url",
                json={"access_token": "stub_access_code"},
                headers={"content-type": "application/json"},
            )
            m.get(
                "http://localhost:8000/goosetools/stub_discord_auth/profile_url",
                json={
                    "id": "UNKNOWN",
                    "username": "TEST USER",
                    "avatar": "e71b856158d285d6ac6e8877d17bae45",
                    "discriminator": "1234",
                    "public_flags": 0,
                    "flags": 0,
                    "locale": "en-US",
                    "mfa_enabled": True,
                },
                headers={"content-type": "application/json"},
            )
            self.client.logout()
            response = self.client.get("/goosetools/", follow=True)
            last_url, _ = response.redirect_chain[-1]
            self.post(
                last_url,
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "broker_fee": 3,
                    "username": "test",
                },
            )
            response = self.client.get(reverse("fleet"))
            self.assert_messages(
                response,
                [
                    ("success", "Successfully signed in as test."),
                    ("error", "You are not yet approved and cannot access this page."),
                ],
            )
            self.assertNotIn("Active Fleets", str(response.content, encoding="utf-8"))
