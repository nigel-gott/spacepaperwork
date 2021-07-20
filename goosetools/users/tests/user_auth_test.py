import pytest
import requests_mock
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.test.utils import override_settings
from django.urls.base import reverse
from freezegun import freeze_time

from goosetools.tenants.models import SiteUser
from goosetools.tests.goosetools_test_case import GooseToolsTestCase
from goosetools.users.models import (
    BASIC_ACCESS,
    LOOT_TRACKER,
    USER_ADMIN_PERMISSION,
    Corp,
    DiscordGuild,
    DiscordRole,
    GooseGroup,
    GooseUser,
    UserApplication,
)


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
    def setUp(self):
        super().setUp()
        site, _ = Site.objects.get_or_create(
            id=3, defaults={"domain": "localhost", "name": "localhost"}
        )
        app = SocialApp.objects.create(
            provider="discord",
            name="discord",
            client_id="123456",
            secret="some_rando_key",
            key="",
        )
        app.sites.add(site)
        for site in Site.objects.all():
            app.sites.add(site)
        user_admin_group, _ = GooseGroup.objects.get_or_create(name="user_admin_group")
        user_admin_group.link_permission(USER_ADMIN_PERMISSION)
        self.user_admin_group = user_admin_group

    def test_approved_user_can_see_non_whitelisted_page(self):
        basic_access_group, _ = GooseGroup.objects.get_or_create(name="basic")
        basic_access_group.link_permission(BASIC_ACCESS)
        basic_access_group.link_permission(LOOT_TRACKER)
        self.user.give_group(basic_access_group)
        response = self.client.get(reverse("fleet"))
        self.assertIn("Active Fleets", str(response.content, encoding="utf-8"))
        self.assert_messages(response, [])

    def test_unapproved_user_cant_see_non_whitelisted_page(self):
        self.user.status = "unapproved"
        self.user.save()

        response = self.client.get(reverse("fleet"))
        self.assertNotIn("Active Fleets", str(response.content, encoding="utf-8"))
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
        public_corp = Corp.objects.create(name="public", public_corp=True)
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
                reverse("user_signup", args=[public_corp.pk]),
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "broker_fee": 3,
                    "ingame_name": "My Ingame Name",
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
        DiscordGuild.objects.create(
            guild_id="guild_id",
            active=True,
        )
        basic_access_group, _ = GooseGroup.objects.get_or_create(
            name="basic_access_group_given_on_signup",
            required_discord_role=DiscordRole.objects.create(
                name="member_role_id", role_id="member_role_id"
            ),
        )
        basic_access_group.link_permission(BASIC_ACCESS)
        basic_access_group.link_permission(LOOT_TRACKER)

        public_corp = Corp.objects.create(name="public", public_corp=True)
        with requests_mock.Mocker() as m:
            m.get(
                "https://discord.com/api/guilds/guild_id/members/3",
                json={},
                headers={"content-type": "application/json"},
            )
            m.put(
                "https://discord.com/api/guilds/guild_id/members/3/roles/member_role_id"
            )
            mock_discord_returns_with_uid(m, "3")
            self.client.logout()
            # When an unknown and hence unapproved user applies to the corp
            self.client.get(reverse("discord_login"), follow=True)

            self.post(
                reverse("user_signup", args=[public_corp.pk]),
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "broker_fee": 3,
                    "ingame_name": "My Main",
                },
            )

            self.client.logout()
            self.client.force_login(self.site_user)

            self.user.give_group(self.user_admin_group)

            # Their application can been seen by a user_admin
            applications = self.get(reverse("applications")).context["object_list"]
            self.assertEqual(len(applications), 1)
            application = applications[0]
            self.assertEqual(application.user.username(), "TEST USER#1234")
            self.assertEqual(application.user.discord_uid(), "3")
            self.assertEqual(application.corp, public_corp)
            self.assertEqual(application.ingame_name, "My Main")
            self.assertEqual(application.status, "unapproved")
            m.put(
                "https://discord.com/api/guilds/guild_id/members/3/roles/member_role_id"
            )
            m.get(
                "https://discord.com/api/guilds/guild_id/members/3",
                json={"roles": ["member_role_id"]},
                headers={"content-type": "application/json"},
            )

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
        public_corp = Corp.objects.create(name="public", public_corp=True)
        with requests_mock.Mocker() as m:
            mock_discord_returns_with_uid(m, "3")
            self.client.logout()
            # When an unknown and hence unapproved user applies to the corp
            self.client.get(reverse("discord_login"), follow=True)
            self.post(
                reverse("user_signup", args=[public_corp.pk]),
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "broker_fee": 3,
                    "ingame_name": "My Main",
                },
            )

            self.client.logout()
            self.client.force_login(self.site_user)

            self.user.give_group(self.user_admin_group)
            self.assertEqual(
                UserApplication.objects.filter(status="unapproved").count(), 1
            )

            # Their application can been seen by a user_admin
            applications = self.get(reverse("applications")).context["object_list"]
            self.assertEqual(len(applications), 1)
            application = applications[0]
            self.assertEqual(application.user.username(), "TEST USER#1234")
            self.assertEqual(application.user.discord_uid(), "3")
            self.assertEqual(application.corp, public_corp)
            self.assertEqual(application.ingame_name, "My Main")
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

            self.corp.discord_roles_allowing_application.add(
                DiscordRole.objects.create(role_id="1234", name="test role")
            )
            self.corp.save()
            errors = self.post_expecting_error(
                reverse("user_signup", args=[self.corp.pk]),
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "broker_fee": 3,
                    "ingame_name": "My Main",
                },
            )
            self.assertEqual(
                errors, ["You do not have permissions to apply for that corp."]
            )

    def test_can_apply_to_unrestricted_corp(
        self,
    ):
        public_corp = Corp.objects.create(name="public", public_corp=True)
        with requests_mock.Mocker() as m:
            mock_discord_returns_with_uid(m, "3")
            self.client.logout()
            self.client.get(reverse("discord_login"), follow=True)

            self.corp.discord_roles_allowing_application.clear()
            self.corp.save()
            self.post(
                reverse("user_signup", args=[public_corp.pk]),
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "broker_fee": 3,
                    "username": "test",
                    "ingame_name": "My Main",
                },
            )

    def test_can_apply_to_restricted_corp_if_you_have_roles(
        self,
    ):
        with requests_mock.Mocker() as m:
            mock_discord_returns_with_uid(m, "3", roles=["1234"])
            self.client.logout()
            self.client.get(reverse("discord_login"), follow=True)

            self.corp.discord_roles_allowing_application.add(
                DiscordRole.objects.create(role_id="1234", name="test role")
            )
            self.corp.save()
            self.post(
                reverse("user_signup", args=[self.corp.pk]),
                {
                    "timezone": "Pacific/Niue",
                    "transaction_tax": 14,
                    "broker_fee": 3,
                    "ingame_name": "My Main",
                },
            )

    @override_settings(PRONOUN_ROLES="on", PRONOUN_THEY_DISCORD_ROLE="THEY")
    def test_signing_up_gives_preffered_pronoun_role_if_specified(
        self,
    ):
        public_corp = Corp.objects.create(name="public", public_corp=True)
        with requests_mock.Mocker() as m:
            DiscordGuild.objects.create(
                active=True,
                guild_id="guildid",
            )
            m.get(
                "https://discord.com/api/guilds/guildid/members/3",
                json={"meh": "what"},
                headers={"content-type": "application/json"},
            )
            m.put("https://discord.com/api/guilds/guildid/members/3/roles/THEY")
            mock_discord_returns_with_uid(m, "3", roles=["1234"])
            self.client.logout()
            self.client.get(reverse("discord_login"), follow=True)

            self.post(
                reverse("user_signup", args=[public_corp.pk]),
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
        self.user.give_group(self.user_admin_group)
        public_corp = Corp.objects.create(name="public", public_corp=True)
        UserApplication.objects.create(
            user=self.other_user,
            corp=public_corp,
            ingame_name="TEST",
            status="unapproved",
            answers={},
        )

        # Their application can been seen by a user_admin
        applications = self.get(reverse("applications")).context["object_list"]
        self.assertEqual(len(applications), 1)
        application = applications[0]
        self.post(reverse("application_update", args=[application.pk]), {"approve": ""})
        applications = self.get(reverse("applications")).context["object_list"]
        self.assertEqual(len(applications), 0)

    def test_cant_approve_app_into_corp_where_the_user_cannot_join_as_it_is_not_public(
        self,
    ):
        self.user.give_group(self.user_admin_group)
        private_corp = Corp.objects.create(name="private_corp", public_corp=False)
        UserApplication.objects.create(
            user=self.other_user,
            corp=private_corp,
            ingame_name="TEST",
            status="unapproved",
            answers={},
        )

        # Their application can been seen by a user_admin
        applications = self.get(reverse("applications")).context["object_list"]
        self.assertEqual(len(applications), 1)
        application = applications[0]
        errors = self.post_expecting_error(
            reverse("application_update", args=[application.pk]), {"approve": ""}
        )
        self.assertEqual(
            errors,
            [
                "Cannot approve this application with a in-game name as the user no longer has permission to join the corp in question."
            ],
        )

    def test_approving_an_application_when_the_guild_has_a_member_role_assigns_the_role(
        self,
    ):
        with requests_mock.Mocker() as m:
            DiscordGuild.objects.create(
                active=True,
                guild_id="guildid",
            )
            m.get(
                "https://discord.com/api/guilds/guildid/members/2",
                json={"roles": ["required_memberroleid"]},
                headers={"content-type": "application/json"},
            )
            m.put(
                "https://discord.com/api/guilds/guildid/members/2/roles/memberroleid",
                headers={
                    "Authorization": "Bot bot_token",
                },
            )
            self.user.give_group(self.user_admin_group)
            UserApplication.objects.create(
                user=self.other_user,
                corp=self.corp,
                ingame_name="TEST",
                status="unapproved",
                answers={},
            )
            self.corp.discord_role_given_on_approval = DiscordRole.objects.create(
                role_id="memberroleid", name="role"
            )
            self.corp.discord_roles_allowing_application.add(
                DiscordRole.objects.create(
                    role_id="required_memberroleid", name="required"
                )
            )
            self.corp.save()

            # Their application can been seen by a user_admin
            applications = self.get(reverse("applications")).context["object_list"]
            self.assertEqual(len(applications), 1)
            application = applications[0]
            self.post(
                reverse("application_update", args=[application.pk]), {"approve": ""}
            )
            applications = self.get(reverse("applications")).context["object_list"]
            self.assertEqual(len(applications), 0)
