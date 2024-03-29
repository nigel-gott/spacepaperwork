import requests_mock
from django.urls.base import reverse
from requests.adapters import Response

from goosetools.tests.goosetools_test_case import GooseToolsTestCase
from goosetools.venmo.models import VirtualCurrency


class VenmoTest(GooseToolsTestCase):
    def setUp(self):
        super().setUp()
        VirtualCurrency.objects.create(name="eggs", api_type="fog_venmo", default=True)

    def test_uses_django_setting_to_control_venmo_host_location_and_api_token(self):
        uid = self.user.discord_uid()
        with requests_mock.Mocker() as mock:
            with self.settings(
                VENMO_HOST_URL="some_other_host.com",
                VENMO_API_TOKEN="venmo_secret",
                VENMO_BASE_PATH="/dev",
            ):
                # pylint: disable=inconsistent-return-statements
                def match_api_token_header(request):
                    if request.headers.get("x-api-key") == "venmo_secret":
                        return True
                    resp = Response()
                    resp.status_code = 403
                    print(
                        f"Missing header x-api-token or invalid token, headers were: {request.headers}"
                    )
                    resp.raise_for_status()

                mock.get(
                    f"https://some_other_host.com/dev/users/{uid}",
                    json={
                        "discordId": uid,
                        "balance": 10,
                        "netPendingChange": 0,
                        "availableBalance": 10,
                        "createdAt": "2021-01-24T19:44:21.123Z",
                        "updatedAt": "2021-01-24T19:44:21.456Z",
                    },
                    headers={
                        "content-type": "application/json",
                    },
                    additional_matcher=match_api_token_header,
                )
                response = self.get(reverse("venmo:dashboard", args=["default"]))
                self.assertIn(
                    "Current Balance: Ƶ 10", str(response.content, encoding="utf-8")
                )

    def test_when_displaying_the_users_transactions_venmo_server_is_queried_for_the_users_balance(
        self,
    ):
        with requests_mock.Mocker() as mock:
            with self.settings(
                VENMO_HOST_URL="some_other_host.com",
                VENMO_API_TOKEN="venmo_secret",
                VENMO_BASE_PATH="/dev",
            ):
                uid = self.user.discord_uid()
                mock.get(
                    f"https://some_other_host.com/dev/users/{uid}",
                    json={
                        "discordId": uid,
                        "balance": 10,
                        "netPendingChange": 0,
                        "availableBalance": 10,
                        "createdAt": "2021-01-24T19:44:21.123Z",
                        "updatedAt": "2021-01-24T19:44:21.456Z",
                    },
                    headers={
                        "content-type": "application/json",
                    },
                )
                response = self.get(reverse("venmo:dashboard", args=["default"]))
                self.assertIn(
                    "Current Balance: Ƶ 10", str(response.content, encoding="utf-8")
                )
