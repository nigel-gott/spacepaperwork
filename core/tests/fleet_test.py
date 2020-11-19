from django.urls.base import reverse
from freezegun import freeze_time

from core.tests.goosetools_test_case import GooseToolsTestCase


@freeze_time("2012-01-14 12:00:00")
class FleetTest(GooseToolsTestCase):
    def an_open_fleet(self):
        return self.a_fleet(start_date="Jan. 14, 2012", start_time="11:02 AM")

    def test_can_make_a_fleet(self):
        response = self.client.post(
            reverse("fleet_create"),
            {
                "start_date": "Jan. 14, 2012",
                "start_time": "11:02 AM",
                "fleet_type": self.fleet_type.id,
                "fc_character": self.char.id,
                "loot_type": "Master Looter",
                "name": "My Fleet Name",
                "description": "My Description",
                "location": "My Location",
                "expected_duration": "My Expected Duration",
                "gives_shares_to_alts": False,
                "loot_was_stolen": False,
            },
        )
        self.assertEqual(response.status_code, 302)

        fleets_view = self.client.get(response.url)

        expected_fleet = fleets_view.context["fleets"].get()
        self.assertEqual(expected_fleet.name, "My Fleet Name")
        self.assertEqual(expected_fleet.fc, self.logged_in_user)
        self.assertEqual(expected_fleet.fleet_type, self.fleet_type)
        self.assertEqual(expected_fleet.loot_type, "Master Looter")
        self.assertEqual(expected_fleet.gives_shares_to_alts, False)
        self.assertEqual(expected_fleet.loot_was_stolen, False)
        self.assertEqual(str(expected_fleet.start), "2012-01-14 11:02:00+00:00")
        self.assertIsNone(expected_fleet.end)
        self.assertEqual(expected_fleet.description, "My Description")
        self.assertEqual(expected_fleet.location, "My Location")
        self.assertEqual(expected_fleet.expected_duration, "My Expected Duration")

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

        join_response = self.post(
            reverse("fleet_join", args=[fleet.id]), {"character": self.other_char.id}
        )
        self.assertEqual(join_response.status_code, 302)

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
        fleet = self.test_can_join_fleet()
        fleet_view_before_leaving = self.get(
            reverse("fleet_view", args=[fleet.id]),
        )
        fleet_member_to_leave = fleet_view_before_leaving.context[
            "fleet_members_by_id"
        ][self.other_discord_user.id][0]
        leave_response = self.post(
            reverse("fleet_leave", args=[fleet_member_to_leave.id])
        )
        self.assertEqual(leave_response.status_code, 302)
        fleet_view = self.get(
            reverse("fleet_view", args=[fleet.id]),
        )
        self.assertNotIn(
            self.other_discord_user.id, fleet_view.context["fleet_members_by_id"]
        )

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
