import pytest
import requests_mock
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.urls.base import reverse
from freezegun import freeze_time

from goosetools.tenants.models import SiteUser
from goosetools.tests.goosetools_test_case import GooseToolsTestCase
from goosetools.users.models import DiscordGuild, GooseUser, UserApplication


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

    def test_approved_user_can_see_non_whitelisted_page(self):
        response = self.client.get(reverse("fleet"))
        self.assertIn("Active Fleets", str(response.content, encoding="utf-8"))
        self.assert_messages(response, [])

    def test_unapproved_user_cant_see_non_whitelisted_page(self):
        self.user.status = "unapproved"
        self.user.save()

        response = self.client.get(reverse("fleet"))
        self.assertNotIn("Active Fleets", str(response.content, encoding="utf-8"))
        self.assertRedirects(response, reverse("core:home"))
        self.assert_messages(
            response,
            [("error", "You are not yet approved and cannot access this page.")],
        )

    def test_a_users_username_is_based_off_their_extra_profile_data(self):
        with requests_mock.Mocker() as m:
            mock_discord_returns_with_uid(
                m, "3", profile_username="CUSTOMUSERNAME", profile_discriminator="1111"
            )
            self.client.logout()
            response = self.client.get(reverse("discord_login"), follow=True)
            self.assert_messages(
                response,
                [
                    ("success", "Successfully signed in as CUSTOMUSERNAME#1111."),
                ],
            )

    def test_a_logging_in_with_a_different_username_updates_your_username(self):
        with requests_mock.Mocker() as m:
            mock_discord_returns_with_uid(
                m, "3", profile_username="CUSTOMUSERNAME", profile_discriminator="1111"
            )
            self.client.logout()
            response = self.client.get(reverse("discord_login"), follow=True)

            self.assert_messages(
                response,
                [
                    ("success", "Successfully signed in as CUSTOMUSERNAME#1111."),
                ],
            )
            mock_discord_returns_with_uid(
                m, "3", profile_username="NEWUSERNAME", profile_discriminator="1111"
            )
            self.client.logout()
            response = self.client.get(reverse("discord_login"), follow=True)
            self.assert_messages(
                response,
                [
                    ("success", "Successfully signed in as NEWUSERNAME#1111."),
                ],
            )

    def test_signing_up_with_an_already_taken_username_errors(self):
        with requests_mock.Mocker() as m:
            mock_discord_returns_with_uid(
                m, "3", profile_username="CUSTOMUSERNAME", profile_discriminator="1111"
            )
            self.client.logout()
            response = self.client.get(reverse("discord_login"), follow=True)
            self.assert_messages(
                response,
                [
                    ("success", "Successfully signed in as CUSTOMUSERNAME#1111."),
                ],
            )

            mock_discord_returns_with_uid(
                m, "4", profile_username="CUSTOMUSERNAME", profile_discriminator="1111"
            )
            self.client.logout()
            with pytest.raises(
                ValidationError,
                match=r"User already exists with CUSTOMUSERNAME#1111 username cannot change CUSTOMUSERNAME to match.",
            ):
                self.client.get(reverse("discord_login"), follow=True)

    def test_an_unknown_discord_user_is_unapproved_after_signing_up(self):
        with requests_mock.Mocker() as m:
            mock_discord_returns_with_uid(m, "3")
            self.client.logout()
            response = self.client.get(reverse("discord_login"), follow=True)
            self.assert_messages(
                response,
                [
                    ("success", "Successfully signed in as TEST USER#1234."),
                ],
            )

            self.post(
                reverse("user_signup"),
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "broker_fee": 3,
                    "ingame_name": "My Ingame Name",
                    "activity": "a",
                    "previous_alliances": "a",
                    "looking_for": "a",
                    "corp": self.corp.pk,
                },
            )
            response = self.client.get(reverse("fleet"))
            self.assert_messages(
                response,
                [
                    ("error", "You are not yet approved and cannot access this page."),
                ],
            )
            self.assertNotIn("Active Fleets", str(response.content, encoding="utf-8"))

    def test_unknown_user_creates_an_app_on_signup_which_can_be_approved(
        self,
    ):
        with requests_mock.Mocker() as m:
            mock_discord_returns_with_uid(m, "3")
            self.client.logout()
            # When an unknown and hence unapproved user applies to the corp
            self.client.get(reverse("discord_login"), follow=True)

            self.post(
                reverse("user_signup"),
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "broker_fee": 3,
                    "ingame_name": "My Main",
                    "activity": "a",
                    "previous_alliances": "a",
                    "looking_for": "a",
                    "corp": self.corp.pk,
                    "application_notes": "Hello please let me into goosefleet",
                },
            )

            self.client.logout()
            self.client.force_login(self.site_user)

            user_admin_group = Group.objects.get(name="user_admin")
            self.site_user.groups.add(user_admin_group)

            # Their application can been seen by a user_admin
            applications = self.get(reverse("applications")).context["object_list"]
            self.assertEqual(len(applications), 1)
            application = applications[0]
            self.assertEqual(application.user.username(), "TEST USER#1234")
            self.assertEqual(application.user.discord_uid(), "3")
            self.assertEqual(application.corp, self.corp)
            self.assertEqual(application.ingame_name, "My Main")
            self.assertEqual(
                application.application_notes, "Hello please let me into goosefleet"
            )
            self.assertEqual(application.status, "unapproved")

            self.post(
                reverse("application_update", args=[application.pk]),
                {"approve": "", "notes": "Test Notes"},
            )
            new_user = GooseUser.objects.get(site_user__username="TEST USER#1234")
            self.assertEqual(new_user.notes, "Test Notes")
            self.client.force_login(new_user.site_user)
            response = self.client.get(reverse("fleet"))
            self.assertIn("Active Fleets", str(response.content, encoding="utf-8"))

    def test_unknown_user_creates_an_app_on_signup_which_can_be_rejected(
        self,
    ):
        with requests_mock.Mocker() as m:
            mock_discord_returns_with_uid(m, "3")
            self.client.logout()
            # When an unknown and hence unapproved user applies to the corp
            self.client.get(reverse("discord_login"), follow=True)
            self.post(
                reverse("user_signup"),
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "broker_fee": 3,
                    "activity": "a",
                    "previous_alliances": "a",
                    "looking_for": "a",
                    "ingame_name": "My Main",
                    "corp": self.corp.pk,
                    "application_notes": "Hello please let me into goosefleet",
                },
            )

            self.client.logout()
            self.client.force_login(self.site_user)

            user_admin_group = Group.objects.get(name="user_admin")
            self.site_user.groups.add(user_admin_group)
            self.assertEqual(
                UserApplication.objects.filter(status="unapproved").count(), 1
            )

            # Their application can been seen by a user_admin
            applications = self.get(reverse("applications")).context["object_list"]
            self.assertEqual(len(applications), 1)
            application = applications[0]
            self.assertEqual(application.user.username(), "TEST USER#1234")
            self.assertEqual(application.user.discord_uid(), "3")
            self.assertEqual(application.corp, self.corp)
            self.assertEqual(application.ingame_name, "My Main")
            self.assertEqual(
                application.application_notes, "Hello please let me into goosefleet"
            )
            self.assertEqual(application.status, "unapproved")

            self.post(
                reverse("application_update", args=[application.pk]), {"reject": ""}
            )
            self.client.force_login(SiteUser.objects.get(username="TEST USER#1234"))
            response = self.client.get(reverse("fleet"))
            self.assert_messages(
                response,
                [
                    ("error", "You are not yet approved and cannot access this page."),
                ],
            )
            self.assertNotIn("Active Fleets", str(response.content, encoding="utf-8"))

    def test_cant_apply_for_restricted_corp_if_user_doesnt_have_role(
        self,
    ):
        with requests_mock.Mocker() as m:
            mock_discord_returns_with_uid(m, "3")
            self.client.logout()
            self.client.get(reverse("discord_login"), follow=True)

            self.corp.required_discord_role = "1234"
            self.corp.save()
            errors = self.client.post(
                reverse("user_signup"),
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "activity": "a",
                    "previous_alliances": "a",
                    "looking_for": "a",
                    "broker_fee": 3,
                    "ingame_name": "My Main",
                    "corp": self.corp.pk,
                    "application_notes": "Hello please let me into goosefleet",
                },
            )
            self.assertEqual(
                errors.context["form"].errors.as_json(),
                '{"corp": [{"message": "Select a valid choice. That choice is not one of the available choices.", "code": "invalid_choice"}]}',
            )

    def test_can_apply_to_unrestricted_corp(
        self,
    ):
        with requests_mock.Mocker() as m:
            mock_discord_returns_with_uid(m, "3")
            self.client.logout()
            self.client.get(reverse("discord_login"), follow=True)

            self.corp.required_discord_role = None
            self.corp.save()
            self.post(
                reverse("user_signup"),
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "activity": "a",
                    "previous_alliances": "a",
                    "looking_for": "a",
                    "broker_fee": 3,
                    "username": "test",
                    "ingame_name": "My Main",
                    "corp": self.corp.pk,
                    "application_notes": "Hello please let me into goosefleet",
                },
            )

    def test_can_apply_to_unrestricted_corp_with_blank_role(
        self,
    ):
        with requests_mock.Mocker() as m:
            mock_discord_returns_with_uid(m, "3")
            self.client.logout()
            self.client.get(reverse("discord_login"), follow=True)

            self.corp.required_discord_role = ""
            self.corp.save()
            self.post(
                reverse("user_signup"),
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "activity": "a",
                    "previous_alliances": "a",
                    "looking_for": "a",
                    "broker_fee": 3,
                    "ingame_name": "My Main",
                    "corp": self.corp.pk,
                    "application_notes": "Hello please let me into goosefleet",
                },
            )

    def test_can_apply_to_restricted_corp_if_you_have_roles(
        self,
    ):
        with requests_mock.Mocker() as m:
            mock_discord_returns_with_uid(m, "3", roles=["1234"])
            self.client.logout()
            self.client.get(reverse("discord_login"), follow=True)

            self.corp.required_discord_role = "1234"
            self.corp.save()
            self.post(
                reverse("user_signup"),
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "activity": "a",
                    "previous_alliances": "a",
                    "looking_for": "a",
                    "broker_fee": 3,
                    "ingame_name": "My Main",
                    "corp": self.corp.pk,
                    "application_notes": "Hello please let me into goosefleet",
                },
            )

    def test_signing_up_gives_preffered_pronoun_role_if_specified(
        self,
    ):
        with requests_mock.Mocker() as m:
            DiscordGuild.objects.create(
                active=True,
                bot_token="bot_token",
                guild_id="guildid",
                member_role_id="memberroleid",
            )
            m.get(
                "https://discord.com/api/guilds/guildid/members/3",
                json={"meh": "what"},
                headers={"content-type": "application/json"},
            )
            m.put(
                "https://discord.com/api/guilds/guildid/members/3/roles/762405572136927242"
            )
            mock_discord_returns_with_uid(m, "3", roles=["1234"])
            self.client.logout()
            self.client.get(reverse("discord_login"), follow=True)

            self.post(
                reverse("user_signup"),
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "activity": "a",
                    "previous_alliances": "a",
                    "looking_for": "a",
                    "broker_fee": 3,
                    "prefered_pronouns": "they",
                    "ingame_name": "My Main",
                    "corp": self.corp.pk,
                    "application_notes": "Hello please let me into goosefleet",
                },
            )

    def test_once_an_application_has_been_approved_it_disappears_from_the_applications_screen(
        self,
    ):
        user_admin_group = Group.objects.get(name="user_admin")
        self.site_user.groups.add(user_admin_group)
        UserApplication.objects.create(
            user=self.other_user,
            corp=self.corp,
            ingame_name="TEST",
            status="unapproved",
        )

        # Their application can been seen by a user_admin
        applications = self.get(reverse("applications")).context["object_list"]
        self.assertEqual(len(applications), 1)
        application = applications[0]
        self.post(reverse("application_update", args=[application.pk]), {"approve": ""})
        applications = self.get(reverse("applications")).context["object_list"]
        self.assertEqual(len(applications), 0)

    def test_approving_an_application_when_the_guild_has_a_member_role_assigns_the_role(
        self,
    ):
        with requests_mock.Mocker() as m:
            DiscordGuild.objects.create(
                active=True,
                bot_token="bot_token",
                guild_id="guildid",
                member_role_id="memberroleid",
            )
            m.put(
                "https://discord.com/api/guilds/guildid/members/2/roles/memberroleid",
                headers={
                    "Authorization": "Bot bot_token",
                },
            )
            user_admin_group = Group.objects.get(name="user_admin")
            self.site_user.groups.add(user_admin_group)
            UserApplication.objects.create(
                user=self.other_user,
                corp=self.corp,
                ingame_name="TEST",
                status="unapproved",
            )

            # Their application can been seen by a user_admin
            applications = self.get(reverse("applications")).context["object_list"]
            self.assertEqual(len(applications), 1)
            application = applications[0]
            self.post(
                reverse("application_update", args=[application.pk]), {"approve": ""}
            )
            applications = self.get(reverse("applications")).context["object_list"]
            self.assertEqual(len(applications), 0)
