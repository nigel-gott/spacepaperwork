from django.urls.base import reverse
from freezegun import freeze_time

from core.tests.goosetools_test_case import GooseToolsTestCase


@freeze_time("2012-01-14 12:00:00")
class FleetTest(GooseToolsTestCase):
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
        fleet_view = self.client.get(
            reverse("fleet_view", args=[fleet.id]),
        )
        self.assertEqual(fleet.id, fleet_view.context["fleet"].id)
        self.assertIn(self.discord_user.id, fleet_view.context["fleet_members_by_id"])
        self.assertIn(self.discord_user.username, str(fleet_view.content))
