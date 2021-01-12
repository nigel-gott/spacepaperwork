from django.urls.base import reverse
from freezegun import freeze_time

from goosetools.tests.goosetools_test_case import GooseToolsTestCase
from goosetools.users.models import Character, DiscordUser


@freeze_time("2012-01-14 12:00:00")
class FleetTest(GooseToolsTestCase):
    def an_open_fleet(self, gives_shares_to_alts=False):
        return self.a_fleet(
            start_date="Jan. 14, 2012",
            start_time="11:02 AM",
            gives_shares_to_alts=gives_shares_to_alts,
        )

    def test_can_make_a_fleet(self):
        response = self.post(
            reverse("fleet_create"),
            {
                "start_date": "Jan. 14, 2012",
                "start_time": "11:02 AM",
                "fc_character": self.char.id,
                "loot_type": "Master Looter",
                "name": "My Fleet Name",
                "description": "My Description",
                "location": "My Location",
                "expected_duration": "My Expected Duration",
                "gives_shares_to_alts": False,
            },
        )

        created_fleet = self.get(response.url).context["fleet"]
        self.assertEqual(created_fleet.name, "My Fleet Name")
        self.assertEqual(created_fleet.fc, self.logged_in_user)
        self.assertEqual(created_fleet.loot_type, "Master Looter")
        self.assertEqual(created_fleet.gives_shares_to_alts, False)
        self.assertEqual(str(created_fleet.start), "2012-01-14 11:02:00+00:00")
        self.assertIsNone(created_fleet.end)
        self.assertEqual(created_fleet.description, "My Description")
        self.assertEqual(created_fleet.location, "My Location")
        self.assertEqual(created_fleet.expected_duration, "My Expected Duration")

    def test_cant_make_a_fleet_where_end_is_less_than_start(self):
        error = self.post_expecting_error(
            reverse("fleet_create"),
            {
                "start_date": "Jan. 14, 2012",
                "start_time": "11:02 AM",
                "end_date": "Jan. 13, 2012",
                "end_time": "11:02 AM",
                "fc_character": self.char.id,
                "loot_type": "Master Looter",
                "name": "My Fleet Name",
                "description": "My Description",
                "location": "My Location",
                "expected_duration": "My Expected Duration",
                "gives_shares_to_alts": False,
            },
        )
        self.assertEqual(
            error,
            ["The fleet start time must be before the fleet end time!"],
        )

    def test_cant_edit_a_fleet_so_that_end_is_less_than_start(self):
        fleet = self.a_fleet()
        error = self.post_expecting_error(
            reverse("fleet_edit", args=[fleet.pk]),
            {
                "start_date": "Jan. 14, 2012",
                "start_time": "11:02 AM",
                "end_date": "Jan. 13, 2012",
                "end_time": "11:02 AM",
                "fc_character": self.char.id,
                "loot_type": "Master Looter",
                "name": "My Fleet Name",
                "description": "My Description",
                "location": "My Location",
                "expected_duration": "My Expected Duration",
                "gives_shares_to_alts": False,
            },
        )
        self.assertEqual(
            error,
            ["The fleet start time must be before the fleet end time!"],
        )

    def test_can_edit_a_fleet(self):
        fleet = self.a_fleet()
        response = self.post(
            reverse("fleet_edit", args=[fleet.pk]),
            {
                "start_date": "Jan. 14, 1900",
                "start_time": "08:02 PM",
                "end_date": "Jan. 14, 1900",
                "fc_character": self.char.id,
                "end_time": "10:02 PM",
                "loot_type": "Free For All",
                "name": "Another Fleet Name",
                "description": "Another My Description",
                "location": "Another My Location",
                "expected_duration": "Another My Expected Duration",
                "gives_shares_to_alts": True,
            },
        )
        self.assertEqual(response.status_code, 302)

        fleet.refresh_from_db()
        self.assertEqual(fleet.name, "Another Fleet Name")
        self.assertEqual(fleet.fc, self.logged_in_user)
        self.assertEqual(fleet.loot_type, "Free For All")
        self.assertEqual(fleet.gives_shares_to_alts, True)
        self.assertEqual(str(fleet.start), "1900-01-14 20:03:00+00:00")
        self.assertEqual(str(fleet.end), "1900-01-14 22:03:00+00:00")
        self.assertEqual(fleet.description, "Another My Description")
        self.assertEqual(fleet.location, "Another My Location")
        self.assertEqual(fleet.expected_duration, "Another My Expected Duration")

    def test_fc_member_of_fleet_by_default(self):
        fleet = self.a_fleet()
        fleet_view = self.get(
            reverse("fleet_view", args=[fleet.id]),
        )
        self.assertEqual(fleet.id, fleet_view.context["fleet"].id)
        self.assertIn(self.discord_user.id, fleet_view.context["fleet_members_by_id"])
        self.assertIn(self.discord_user.username, str(fleet_view.content))

    def test_can_join_fleet(self):
        fleet = self.an_open_fleet()

        self.client.force_login(self.other_user)

        self.post(
            reverse("fleet_join", args=[fleet.id]), {"character": self.other_char.id}
        )

        fleet_view = self.get(
            reverse("fleet_view", args=[fleet.id]),
        )
        self.assertEqual(fleet.id, fleet_view.context["fleet"].id)
        self.assertIn(
            self.other_discord_user.id, fleet_view.context["fleet_members_by_id"]
        )
        self.assertIn(self.other_discord_user.username, str(fleet_view.content))
        return fleet

    def test_can_leave_fleet(self):
        # When someone has joined a fleet
        fleet = self.test_can_join_fleet()
        fleet_view_before_leaving = self.get(
            reverse("fleet_view", args=[fleet.id]),
        )

        # Then a fleet member leaves it
        fleet_member_to_leave = fleet_view_before_leaving.context[
            "fleet_members_by_id"
        ][self.other_discord_user.id][0]
        self.post(reverse("fleet_leave", args=[fleet_member_to_leave.id]))

        # They no longer are in the fleet as a member
        fleet_view = self.get(
            reverse("fleet_view", args=[fleet.id]),
        )
        self.assertNotIn(
            self.other_discord_user.id, fleet_view.context["fleet_members_by_id"]
        )

    @freeze_time("2012-01-14 03:00:01")
    def test_cant_join_a_fleet_which_has_ended(self):
        a_closed_fleet = self.a_fleet(
            start_date="Jan. 14, 2012",
            start_time="1:00 AM",
            end_date="Jan. 14, 2012",
            end_time="2:00 AM",
        )
        self.client.force_login(self.other_user)
        errors = self.post_expecting_error(
            reverse("fleet_join", args=[a_closed_fleet.id]),
            {"character": self.other_char.id},
        )
        self.assertTrue(a_closed_fleet.in_the_past())
        self.assertEqual(errors, ["Error Joining Fleet: Fleet is Closed"])

    @freeze_time("2012-01-14 13:00:01")
    def test_after_12_hours_a_non_explicitly_closed_fleet_is_automatically_closed(self):
        an_auto_closed_fleet = self.a_fleet(
            start_date="Jan. 14, 2012", start_time="1:00 AM"
        )

        fleet_view = self.get(
            reverse("fleet_view", args=[an_auto_closed_fleet.id]),
        )
        self.assertIn(
            "End: Jan. 14, 2012, 1 p.m. (Automatically expired after 12 hours)",
            str(fleet_view.content),
        )

    @freeze_time("2012-01-14 13:00:01")
    def test_cant_join_a_fleet_which_has_automatically_ended(self):
        an_auto_closed_fleet = self.a_fleet(
            start_date="Jan. 14, 2012",
            start_time="1:00 AM",
        )
        self.client.force_login(self.other_user)
        errors = self.post_expecting_error(
            reverse("fleet_join", args=[an_auto_closed_fleet.id]),
            {"character": self.other_char.id},
        )
        self.assertTrue(an_auto_closed_fleet.in_the_past())
        self.assertEqual(errors, ["Error Joining Fleet: Fleet is Closed"])

    @freeze_time("2012-01-14 12:00:00")
    def test_can_end_a_fleet(self):
        open_fleet = self.an_open_fleet()

        self.post(reverse("fleet_end", args=[open_fleet.id]))

        fleet_view = self.get(reverse("fleet_view", args=[open_fleet.id]))
        open_fleet.refresh_from_db()
        self.assertTrue(open_fleet.in_the_past())
        self.assertIn(
            "End: Jan. 14, 2012, noon (Ends Now)",
            str(fleet_view.content),
        )

    @freeze_time("2012-01-14 12:00:00")
    def test_can_open_a_closed_fleet(self):
        a_closed_fleet = self.a_fleet(
            start_date="Jan. 13, 2012",
            start_time="1:00 AM",
        )

        self.post(reverse("fleet_open", args=[a_closed_fleet.id]))

        fleet_view = self.get(reverse("fleet_view", args=[a_closed_fleet.id]))
        a_closed_fleet.refresh_from_db()
        self.assertFalse(a_closed_fleet.in_the_past())
        self.assertIn(
            "Start: Jan. 14, 2012, noon (Starts Now)",
            str(fleet_view.content),
        )
        self.assertNotIn(
            "End:",
            str(fleet_view.content),
        )

    @freeze_time("2012-01-14 12:00:00")
    def test_cant_open_an_open_fleet(self):
        a_closed_fleet = self.a_fleet(
            start_date="Jan. 14, 2012",
            start_time="1:00 AM",
        )

        errors = self.post_expecting_error(
            reverse("fleet_open", args=[a_closed_fleet.id])
        )
        self.assertEqual(errors, ["You cannot open an already open fleet"])

    @freeze_time("2012-01-14 12:00:00")
    def test_cant_end_a_future_fleet(self):
        a_future_fleet = self.a_fleet(
            start_date="Jan. 15, 2012",
            start_time="1:00 AM",
        )

        errors = self.post_expecting_error(
            reverse("fleet_end", args=[a_future_fleet.id])
        )
        self.assertEqual(
            errors, ["You cannot end a future fleet or one that is already closed."]
        )

    @freeze_time("2012-01-14 12:00:00")
    def test_cant_end_a_past_fleet(self):
        a_future_fleet = self.a_fleet(
            start_date="Jan. 11, 2012",
            start_time="1:00 AM",
        )

        errors = self.post_expecting_error(
            reverse("fleet_end", args=[a_future_fleet.id])
        )
        self.assertEqual(
            errors, ["You cannot end a future fleet or one that is already closed."]
        )

    def test_cant_join_fleet_not_accepting_alts_with_two_characters(self):
        fleet = self.an_open_fleet(gives_shares_to_alts=False)

        self.client.force_login(self.other_user)

        self.post(
            reverse("fleet_join", args=[fleet.id]), {"character": self.other_char.id}
        )
        errors = self.post_expecting_error(
            reverse("fleet_join", args=[fleet.id]),
            {"character": self.other_alt_char.id},
        )
        self.assertEqual(
            errors,
            [
                "Error Joining Fleet: You already have one character "
                "(Test Char 2) in the fleet and you cannot join any more as the fleet doesn't "
                "allow alts."
            ],
        )

    def test_can_join_fleet_accepting_alts_with_two_characters(self):
        fleet = self.an_open_fleet(gives_shares_to_alts=True)

        self.client.force_login(self.other_user)

        self.post(
            reverse("fleet_join", args=[fleet.id]), {"character": self.other_char.id}
        )
        self.post(
            reverse("fleet_join", args=[fleet.id]),
            {"character": self.other_alt_char.id},
        )

        fleet_view = self.get(
            reverse("fleet_view", args=[fleet.id]),
        )
        self.assertEqual(
            [
                c.character.ingame_name
                for c in fleet_view.context["fleet_members_by_id"][
                    self.other_discord_user.id
                ]
            ],
            ["Test Char 2", "Test Alt Char 2"],
        )

    def test_can_leave_a_fleet_with_just_one_alt(self):
        fleet = self.an_open_fleet(gives_shares_to_alts=True)

        self.client.force_login(self.other_user)

        self.post(
            reverse("fleet_join", args=[fleet.id]), {"character": self.other_char.id}
        )
        self.post(
            reverse("fleet_join", args=[fleet.id]),
            {"character": self.other_alt_char.id},
        )

        other_users_fleet_members = self.get_fleet_members_for_user(
            fleet, self.other_discord_user
        )
        self.assertEqual(
            [c.character.ingame_name for c in other_users_fleet_members],
            ["Test Char 2", "Test Alt Char 2"],
        )

        self.post(reverse("fleet_leave", args=[other_users_fleet_members[0].id]))

        other_users_fleet_members = self.get_fleet_members_for_user(
            fleet, self.other_discord_user
        )
        self.assertEqual(
            [c.character.ingame_name for c in other_users_fleet_members],
            ["Test Alt Char 2"],
        )

    def get_fleet_members_for_user(self, fleet, discord_user):
        fleet_view = self.get(
            reverse("fleet_view", args=[fleet.id]),
        )
        fleet_members_by_id = fleet_view.context["fleet_members_by_id"]
        if discord_user.id in fleet_members_by_id:
            return fleet_members_by_id[discord_user.id]
        else:
            return []

    def test_fc_can_make_someone_a_fleet_admin(self):
        fleet = self.a_fleet()
        self.client.force_login(self.other_user)

        self.post(
            reverse("fleet_join", args=[fleet.id]), {"character": self.other_char.id}
        )

        self.client.force_login(self.user)
        other_users_fleet_members = self.get_fleet_members_for_user(
            fleet, self.other_discord_user
        )

        member_to_make_admin = other_users_fleet_members[0]
        self.assertFalse(member_to_make_admin.admin_permissions)
        self.post(reverse("fleet_make_admin", args=[member_to_make_admin.id]))
        member_to_make_admin.refresh_from_db()
        self.assertTrue(member_to_make_admin.admin_permissions)

    def test_fc_can_remove_someone_as_fleet_admin(self):
        fleet = self.there_is_a_fleet_where_other_user_is_an_admin()
        other_users_fleet_members = self.get_fleet_members_for_user(
            fleet, self.other_discord_user
        )

        admin = other_users_fleet_members[0]
        self.assertTrue(admin.admin_permissions)
        self.post(reverse("fleet_remove_admin", args=[admin.id]))
        admin.refresh_from_db()
        self.assertFalse(admin.admin_permissions)

    def test_non_admin_cant_make_someone_a_fleet_admin(self):
        fleet = self.a_fleet()
        self.client.force_login(self.other_user)

        self.post(
            reverse("fleet_join", args=[fleet.id]), {"character": self.other_char.id}
        )

        other_users_fleet_members = self.get_fleet_members_for_user(
            fleet, self.other_discord_user
        )

        member_to_make_admin = other_users_fleet_members[0]
        self.assertFalse(member_to_make_admin.admin_permissions)
        errors = self.post_expecting_error(
            reverse("fleet_make_admin", args=[member_to_make_admin.id])
        )
        self.assertEqual(errors, ["You are forbidden to access this."])
        self.assertFalse(member_to_make_admin.admin_permissions)

    def test_fc_can_manually_add_fleet_members(self):
        fleet = self.a_fleet()
        self.post(
            reverse("fleet_add", args=[fleet.id]), {"character": self.other_char.id}
        )
        other_users_fleet_members = self.get_fleet_members_for_user(
            fleet, self.other_discord_user
        )
        self.assertEqual(
            [c.character.ingame_name for c in other_users_fleet_members],
            ["Test Char 2"],
        )

    def test_admin_can_manually_add_fleet_members(self):
        fleet = self.a_fleet()
        self.post(
            reverse("fleet_add", args=[fleet.id]), {"character": self.other_char.id}
        )
        new_fleet_members = self.get_fleet_members_for_user(
            fleet, self.other_discord_user
        )

        member_to_make_admin = new_fleet_members[0]
        self.post(reverse("fleet_make_admin", args=[member_to_make_admin.id]))

        self.client.force_login(self.other_user)

        new_fleet_members = self.get_fleet_members_for_user(
            fleet, self.other_discord_user
        )

        new_discord_user = DiscordUser.objects.create(
            username="A Brand New Test Goose User"
        )

        new_char = Character.objects.create(
            discord_user=new_discord_user,
            ingame_name="New Test Char",
            corp=self.corp,
        )

        self.post(
            reverse("fleet_add", args=[fleet.id]),
            {"character": new_char.id},
        )
        self.assert_fleet_members_for_user_are(
            fleet, new_discord_user, ["New Test Char"]
        )

    def assert_fleet_members_for_user_are(self, fleet, discord_user, expected_members):
        members = self.get_fleet_members_for_user(fleet, discord_user)
        self.assertEqual([c.character.ingame_name for c in members], expected_members)
        return members

    def there_is_a_fleet_where_other_user_is_an_admin(self):
        fleet = self.a_fleet()
        self.post(
            reverse("fleet_add", args=[fleet.id]), {"character": self.other_char.id}
        )
        other_users_fleet_members = self.get_fleet_members_for_user(
            fleet, self.other_discord_user
        )

        member_to_make_admin = other_users_fleet_members[0]
        self.post(reverse("fleet_make_admin", args=[member_to_make_admin.id]))
        return fleet

    def test_admin_can_remove_fleet_members(self):
        fleet = self.there_is_a_fleet_where_other_user_is_an_admin()
        self.client.force_login(self.other_user)

        new_discord_user = DiscordUser.objects.create(
            username="A Brand New Test Goose User"
        )

        new_char = Character.objects.create(
            discord_user=new_discord_user,
            ingame_name="New Test Char",
            corp=self.corp,
        )

        self.post(
            reverse("fleet_add", args=[fleet.id]),
            {"character": new_char.id},
        )
        members = self.assert_fleet_members_for_user_are(
            fleet, new_discord_user, ["New Test Char"]
        )
        self.post(reverse("fleet_leave", args=[members[0].id]))
        self.assert_fleet_members_for_user_are(fleet, new_discord_user, [])

    def test_non_admin_cant_remove_other_fleet_members(self):
        fleet = self.a_fleet()
        new_discord_user = DiscordUser.objects.create(
            username="A Brand New Test Goose User"
        )
        new_char = Character.objects.create(
            discord_user=new_discord_user,
            ingame_name="New Test Char",
            corp=self.corp,
        )
        self.post(
            reverse("fleet_add", args=[fleet.id]),
            {"character": new_char.id},
        )

        self.client.force_login(self.other_user)

        members = self.assert_fleet_members_for_user_are(
            fleet, new_discord_user, ["New Test Char"]
        )
        errors = self.post_expecting_error(reverse("fleet_leave", args=[members[0].id]))
        self.assertEqual(
            errors, ["You do not have permissions to remove that member from the fleet"]
        )
