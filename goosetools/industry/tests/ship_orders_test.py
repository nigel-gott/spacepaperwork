import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.urls.base import reverse
from django.utils import timezone
from freezegun import freeze_time

import goosetools.industry.views
from goosetools.industry.models import OrderLimitGroup, Ship, ShipOrder
from goosetools.tests.goosetools_test_case import GooseToolsTestCase


@freeze_time("2012-01-14 12:00:00")
class ShipOrderTest(GooseToolsTestCase):
    def setUp(self):
        super().setUp()
        self.next_contract_code = 0
        goosetools.industry.views.generate_random_string = self.get_mock_random_1_string
        self.thorax = Ship.objects.create(name="Thorax", tech_level=6)

    def get_mock_random_1_string(self):
        self.next_contract_code = self.next_contract_code + 1
        return "mock_random_" + str(self.next_contract_code)

    def a_ship_order_returning_response(
        self, ship_pk=None, payment_method="eggs", price=None
    ):
        if not ship_pk:
            ship_pk = self.thorax.pk
        args = {
            "ship": ship_pk,
            "quantity": 1,
            "recipient_character": self.char.pk,
            "payment_method": payment_method,
            "notes": "",
        }
        if price:
            args["isk_price"] = price
            args["eggs_price"] = price
        r = self.post(reverse("industry:shiporders_create"), args)
        ship_order = ShipOrder.objects.last()
        self.post(reverse("industry:shiporders_contract_confirm", args=[ship_order.pk]))
        return r

    def a_ship_order(self, ship_pk=None, payment_method="eggs", price=None):
        self.a_ship_order_returning_response(ship_pk, payment_method, price)
        ship_order = ShipOrder.objects.last()
        return ship_order

    def test_can_order_a_ship(self):
        self.post(
            reverse("industry:shiporders_create"),
            {
                "ship": self.thorax.pk,
                "quantity": 1,
                "recipient_character": self.char.pk,
                "payment_method": "eggs",
                "notes": "",
            },
        )

    def test_can_get_detail_on_model(self):
        ship_order = self.a_ship_order()
        group = Group.objects.get(name="industry")
        self.user.groups.add(group)

        response = self.get(
            reverse("industry:shiporder-detail", args=[ship_order.pk]),
        )
        self.json_matches(
            response,
            f"""{{
        "assignee": null,
        "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
        ],
        "blocked_until": null,
        "created_at": "2012-01-14 12:00",
        "currently_blocked": false,
        "id": {ship_order.pk},
        "notes": "",
        "payment_method": "eggs",
        "quantity": 1,
        "recipient_discord_user_pk": "{self.discord_user.pk}",
        "recipient_character_name": "Test Char",
        "ship": "Thorax",
        "state": "not_started",
        "uid": "Test Discord User-mock_random_1",
        "needs_manual_price": true,
        "payment_taken": false,
        "price": null
 }}""",
        )

    def test_can_list_ship_orders(self):
        ship_order = self.a_ship_order()
        response = self.get(reverse("industry:shiporder-list"))
        self.json_matches(
            response,
            f"""[
     {{
        "assignee": null,
        "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
        ],
        "blocked_until": null,
        "created_at": "2012-01-14 12:00",
        "currently_blocked": false,
        "id": {ship_order.pk},
        "notes": "",
        "payment_method": "eggs",
        "quantity": 1,
        "recipient_discord_user_pk": "{self.discord_user.pk}",
        "recipient_character_name": "Test Char",
        "ship": "Thorax",
        "state": "not_started",
        "uid": "Test Discord User-mock_random_1",
        "needs_manual_price": true,
        "payment_taken": false,
        "price": null
    }}
]""",
        )

    def test_can_claim_ship_order_if_in_industry_group(self):
        ship_order = self.a_ship_order()
        group = Group.objects.get(name="industry")
        self.user.groups.add(group)

        response = self.put(
            reverse("industry:shiporder-claim", args=[ship_order.pk]),
        )
        self.assertEqual(
            str(response.content, encoding="utf-8"),
            f'{{"status":"claimed","assignee":{self.user.pk},"assignee_name":"Test Discord User"}}',
        )

    def test_cant_claim_ship_order_if_not_in_industry_group(self):
        ship_order = self.a_ship_order()
        response = self.client.put(
            reverse("industry:shiporder-claim", args=[ship_order.pk]),
        )
        self.assertEqual(response.status_code, 403)

    def test_cant_claim_already_claimed_ship(self):
        ship_order = self.a_ship_order()
        group = Group.objects.get(name="industry")
        self.user.groups.add(group)
        self.other_user.groups.add(group)

        response = self.put(
            reverse("industry:shiporder-claim", args=[ship_order.pk]),
        )
        self.assertEqual(
            str(response.content, encoding="utf-8"),
            f'{{"status":"claimed","assignee":{self.user.pk},"assignee_name":"Test Discord User"}}',
        )
        self.client.force_login(self.other_user)
        response = self.client.put(
            reverse("industry:shiporder-claim", args=[ship_order.pk]),
        )
        self.assertEqual(
            str(response.content, encoding="utf-8"),
            f'{{"status":"already_claimed","assignee":{self.user.pk},"assignee_name":"{self.user.discord_username()}"}}',
        )

    def test_list_of_ship_orders_shows_assignee_name_after_claiming(self):
        ship_order = self.a_ship_order()
        group = Group.objects.get(name="industry")
        self.user.groups.add(group)
        self.other_user.groups.add(group)

        response = self.put(
            reverse("industry:shiporder-claim", args=[ship_order.pk]),
        )
        response = self.get(reverse("industry:shiporder-list"))
        self.json_matches(
            response,
            f"""[
     {{
        "assignee": {self.user.pk},
        "assignee_name": "{self.user.discord_username()}",
        "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
        ],
        "blocked_until": null,
        "created_at": "2012-01-14 12:00",
        "currently_blocked": false,
        "id": {ship_order.pk},
        "notes": "",
        "payment_method": "eggs",
        "quantity": 1,
        "recipient_discord_user_pk": "{self.discord_user.pk}",
        "recipient_character_name": "Test Char",
        "ship": "Thorax",
        "state": "not_started",
        "uid": "Test Discord User-mock_random_1",
        "needs_manual_price": true,
        "payment_taken": false,
        "price": null
    }}
]""",
        )

    def test_can_unassign_yourself_from_a_ship_order(self):
        ship_order = self.a_ship_order()
        group = Group.objects.get(name="industry")
        self.user.groups.add(group)

        response = self.put(
            reverse("industry:shiporder-claim", args=[ship_order.pk]),
        )
        self.assertEqual(
            str(response.content, encoding="utf-8"),
            f'{{"status":"claimed","assignee":{self.user.pk},"assignee_name":"Test Discord User"}}',
        )
        response = self.put(
            reverse("industry:shiporder-unclaim", args=[ship_order.pk]),
        )
        self.assertEqual(
            str(response.content, encoding="utf-8"), '{"status":"unclaimed"}'
        )

    def test_a_ship_can_be_marked_as_free(self):
        free_ship = Ship.objects.create(name="FreeShip", tech_level=6, free=True)
        ship_order = self.a_ship_order(free_ship.pk, payment_method="free")

        response = self.get(reverse("industry:shiporder-list"))
        self.json_matches(
            response,
            f"""[
     {{
        "assignee": null,
        "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
        ],
        "blocked_until": null,
        "created_at": "2012-01-14 12:00",
        "currently_blocked": false,
        "id": {ship_order.pk},
        "notes": "",
        "payment_method": "free",
        "quantity": 1,
        "recipient_character_name": "Test Char",
        "recipient_discord_user_pk": "{self.discord_user.pk}",
        "ship": "FreeShip",
        "state": "not_started",
        "uid": "Test Discord User-mock_random_1",
        "needs_manual_price": false,
        "payment_taken": true,
        "price": null
    }}
]""",
        )

    def test_ordering_a_nonfree_ship_with_free_method_fails(self):
        paid_ship = Ship.objects.create(name="PaidShip", tech_level=6, free=False)
        r = self.client.post(
            reverse("industry:shiporders_create"),
            {
                "ship": paid_ship.pk,
                "quantity": 1,
                "recipient_character": self.char.pk,
                "payment_method": "free",
                "notes": "",
            },
        )

        self.assert_messages(
            r,
            [
                (
                    "error",
                    "This ship is not free, you must select eggs or isk as a payment method.",
                )
            ],
        )

        r = self.get(reverse("industry:shiporder-list"))
        self.json_matches(
            r,
            "[]",
        )

    def test_ordering_more_than_one_free_ship_fails(self):
        free_ship = Ship.objects.create(name="FreeShip", tech_level=6, free=True)
        r = self.client.post(
            reverse("industry:shiporders_create"),
            {
                "ship": free_ship.pk,
                "quantity": 2,
                "recipient_character": self.char.pk,
                "payment_method": "free",
                "notes": "",
            },
        )

        self.assert_messages(
            r,
            [("error", "You cannot order more than free ship at one time.")],
        )

        r = self.get(reverse("industry:shiporder-list"))
        self.json_matches(
            r,
            "[]",
        )

    @freeze_time("2012-01-14 12:00:00")
    def test_ordering_a_ship_faster_than_its_allowed_frequency_puts_it_in_the_timed_out_state(
        self,
    ):
        order_limit_group = OrderLimitGroup.objects.create(
            days_between_orders=1, name="Free Tech 6 and Below"
        )
        daily_ship = Ship.objects.create(
            name="DailyShip",
            tech_level=6,
            free=True,
            order_limit_group=order_limit_group,
        )

        self.a_ship_order(ship_pk=daily_ship.pk, payment_method="free")
        r = self.client.post(
            reverse("industry:shiporders_create"),
            {
                "ship": daily_ship.pk,
                "quantity": 1,
                "recipient_character": self.char.pk,
                "payment_method": "free",
                "notes": "",
            },
        )
        # The message is shown on the confirm page!
        self.assert_messages(
            r,
            [
                (
                    "warning",
                    "You have already ordered a ship in the 'Free Tech 6 and Below' category within the last 1 days, this order will be blocked until 2012-01-15 12:00:00+00:00.",
                )
            ],
        )
        self.post(
            reverse(
                "industry:shiporders_contract_confirm",
                args=[ShipOrder.objects.last().pk],
            ),
        )
        response = self.get(reverse("industry:shiporder-list"))
        self.json_matches(
            response,
            f"""[
     {{
        "assignee": null,
        "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
        ],
        "blocked_until": null,
        "created_at": "2012-01-14 12:00",
        "currently_blocked": false,
        "id": "IGNORE",
        "notes": "",
        "payment_method": "free",
        "quantity": 1,
        "recipient_discord_user_pk": "{self.discord_user.pk}",
        "recipient_character_name": "Test Char",
        "ship": "DailyShip",
        "state": "not_started",
        "uid": "Test Discord User-mock_random_1",
        "needs_manual_price": false,
        "payment_taken": true,
        "price": null
    }},
     {{
        "assignee": null,
        "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
        ],
        "blocked_until": "2012-01-15 12:00",
        "created_at": "2012-01-14 12:00",
        "currently_blocked": true,
        "id": "IGNORE",
        "notes": "",
        "payment_method": "free",
        "quantity": 1,
        "recipient_discord_user_pk": "{self.discord_user.pk}",
        "recipient_character_name": "Test Char",
        "ship": "DailyShip",
        "state": "not_started",
        "uid": "Test Discord User-mock_random_2",
        "needs_manual_price": false,
        "payment_taken": true,
        "price": null
    }}
]""",
        )

    @freeze_time("2012-01-14 12:00:00")
    # pylint: disable=no-self-use
    def test_cant_add_a_nonfree_ship_to_an_order_limit_group(self):
        order_limit_group = OrderLimitGroup.objects.create(
            days_between_orders=1, name="Free Tech 6 and Below"
        )
        with pytest.raises(
            ValidationError,
            match=r"A Ship cannot be free and in a Order Limit Group. Either remove the group or make the ship free.",
        ):
            Ship.objects.create(
                name="DailyShip",
                tech_level=6,
                free=False,
                order_limit_group=order_limit_group,
            )

    @freeze_time("2012-01-14 12:00:00")
    def test_can_still_order_paid_ships_after_ordering_a_free_one(self):
        order_limit_group = OrderLimitGroup.objects.create(
            days_between_orders=1, name="Free Tech 6 and Below"
        )
        daily_ship = Ship.objects.create(
            name="DailyShip",
            tech_level=6,
            free=True,
            order_limit_group=order_limit_group,
        )

        self.a_ship_order(ship_pk=daily_ship.pk, payment_method="free")
        self.a_ship_order(ship_pk=daily_ship.pk, payment_method="isk")
        self.a_ship_order(ship_pk=daily_ship.pk, payment_method="eggs")
        response = self.get(reverse("industry:shiporder-list"))
        self.json_matches(
            response,
            f"""[
     {{
        "assignee": null,
        "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
        ],
        "blocked_until": null,
        "created_at": "2012-01-14 12:00",
        "currently_blocked": false,
        "id": "IGNORE",
        "notes": "",
        "payment_method": "free",
        "quantity": 1,
        "recipient_discord_user_pk": "{self.discord_user.pk}",
        "recipient_character_name": "Test Char",
        "ship": "DailyShip",
        "state": "not_started",
        "uid": "Test Discord User-mock_random_1",
        "needs_manual_price": false,
        "payment_taken": true,
        "price": null
    }},
     {{
        "assignee": null,
        "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
        ],
        "blocked_until": null,
        "created_at": "2012-01-14 12:00",
        "currently_blocked": false,
        "id": "IGNORE",
        "notes": "",
        "payment_method": "isk",
        "quantity": 1,
        "recipient_discord_user_pk": "{self.discord_user.pk}",
        "recipient_character_name": "Test Char",
        "ship": "DailyShip",
        "state": "not_started",
        "uid": "Test Discord User-mock_random_2",
        "needs_manual_price": true,
        "payment_taken": false,
        "price": null
    }},
     {{
        "assignee": null,
                        "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
        ],
        "blocked_until": null,
        "currently_blocked": false,
        "created_at": "2012-01-14 12:00",
        "id": "IGNORE",
        "notes": "",
        "payment_method": "eggs",
        "quantity": 1,
        "recipient_discord_user_pk": "{self.discord_user.pk}",
        "recipient_character_name": "Test Char",
        "ship": "DailyShip",
        "state": "not_started",
        "uid": "Test Discord User-mock_random_3",
        "needs_manual_price": true,
        "payment_taken": false,
        "price": null
    }}
]""",
        )

    @freeze_time("2012-01-14 12:00:00")
    def test_ordering_multiple_free_limited_ships_queues_them_up(self):
        order_limit_group = OrderLimitGroup.objects.create(
            days_between_orders=1, name="Free Tech 6 and Below"
        )
        daily_ship = Ship.objects.create(
            name="DailyShip",
            tech_level=6,
            free=True,
            order_limit_group=order_limit_group,
        )

        self.a_ship_order(ship_pk=daily_ship.pk, payment_method="free")
        self.a_ship_order(ship_pk=daily_ship.pk, payment_method="free")
        self.a_ship_order(ship_pk=daily_ship.pk, payment_method="free")
        response = self.get(reverse("industry:shiporder-list"))
        self.json_matches(
            response,
            f"""[
     {{
        "assignee": null,
        "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
        ],
        "blocked_until": null,
        "created_at": "2012-01-14 12:00",
        "currently_blocked": false,
        "id": "IGNORE",
        "notes": "",
        "payment_method": "free",
        "quantity": 1,
        "recipient_discord_user_pk": "{self.discord_user.pk}",
        "recipient_character_name": "Test Char",
        "ship": "DailyShip",
        "state": "not_started",
        "uid": "Test Discord User-mock_random_1",
        "needs_manual_price": false,
        "payment_taken": true,
        "price": null
    }},
     {{
        "assignee": null,
        "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
        ],
        "blocked_until": "2012-01-15 12:00",
        "created_at": "2012-01-14 12:00",
        "currently_blocked": true,
        "id": "IGNORE",
        "notes": "",
        "payment_method": "free",
        "quantity": 1,
        "recipient_discord_user_pk": "{self.discord_user.pk}",
        "recipient_character_name": "Test Char",
        "ship": "DailyShip",
        "state": "not_started",
        "uid": "Test Discord User-mock_random_2",
        "needs_manual_price": false,
        "payment_taken": true,
        "price": null
    }},
     {{
        "assignee": null,
                        "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
        ],
        "blocked_until": "2012-01-16 12:00",
        "currently_blocked": true,
        "created_at": "2012-01-14 12:00",
        "id": "IGNORE",
        "notes": "",
        "payment_method": "free",
        "quantity": 1,
        "recipient_discord_user_pk": "{self.discord_user.pk}",
        "recipient_character_name": "Test Char",
        "ship": "DailyShip",
        "state": "not_started",
        "uid": "Test Discord User-mock_random_3",
        "needs_manual_price": false,
        "payment_taken": true,
        "price": null
    }}
]""",
        )

    @freeze_time("2012-01-14 12:00:00")
    def test_ship_availability_is_passed_to_create_ship_order_template(self):
        order_limit_group = OrderLimitGroup.objects.create(
            days_between_orders=1, name="Free Tech 6 and Below"
        )
        daily_ship = Ship.objects.create(
            name="DailyShip",
            tech_level=6,
            free=True,
            order_limit_group=order_limit_group,
        )

        self.a_ship_order(ship_pk=daily_ship.pk, payment_method="free")
        self.a_ship_order(ship_pk=daily_ship.pk, payment_method="free")

        r = self.client.get(
            reverse("industry:shiporders_create"),
        )
        self.assertEqual(
            r.context["ship_data"],
            {
                "Thorax": {
                    "free": False,
                    "tech_level": 6,
                    "isk_price": None,
                    "eggs_price": None,
                    "valid_price": False,
                },
                "DailyShip": {
                    "free": True,
                    "order_limit_group": {
                        "days_between_orders": 1,
                        "name": "Free Tech 6 and Below",
                    },
                    "blocked_until": "2012-01-16 12:00",
                    "tech_level": 6,
                    "isk_price": None,
                    "eggs_price": None,
                    "valid_price": False,
                },
            },
        )

    @freeze_time("2012-01-14 12:00:00")
    def test_cant_claim_a_blocked_ship(self):
        group = Group.objects.get(name="industry")
        self.user.groups.add(group)
        order_limit_group = OrderLimitGroup.objects.create(
            days_between_orders=1, name="Free Tech 6 and Below"
        )
        daily_ship = Ship.objects.create(
            name="DailyShip",
            tech_level=6,
            free=True,
            order_limit_group=order_limit_group,
        )

        self.a_ship_order(ship_pk=daily_ship.pk, payment_method="free")
        blocked_ship = self.a_ship_order(ship_pk=daily_ship.pk, payment_method="free")

        r = self.client.put(
            reverse("industry:shiporder-claim", args=[blocked_ship.pk]),
        )
        self.assertEqual(r.status_code, 400)

    def test_after_past_blocked_until_then_can_claim_previously_blocked_ship(self):
        with freeze_time("2012-01-14 12:00:00") as frozen_time:
            group = Group.objects.get(name="industry")
            self.user.groups.add(group)
            order_limit_group = OrderLimitGroup.objects.create(
                days_between_orders=1, name="Free Tech 6 and Below"
            )
            daily_ship = Ship.objects.create(
                name="DailyShip",
                tech_level=6,
                free=True,
                order_limit_group=order_limit_group,
            )

            self.a_ship_order(ship_pk=daily_ship.pk, payment_method="free")
            blocked_ship = self.a_ship_order(
                ship_pk=daily_ship.pk, payment_method="free"
            )

            r = self.client.put(
                reverse("industry:shiporder-claim", args=[blocked_ship.pk]),
            )
            self.assertEqual(r.status_code, 400)
            frozen_time.move_to("2014-01-15 12:00:01")
            # Tokens expire when moving time in tests!
            self.client.force_login(self.user)
            self.put(
                reverse("industry:shiporder-claim", args=[blocked_ship.pk]),
            )
            blocked_ship.refresh_from_db()
            self.assertEqual(blocked_ship.assignee, self.user)
            self.assertFalse(blocked_ship.currently_blocked())

    def test_order_no_longer_shows_as_blocked_in_list_view_after_time_expires(self):
        with freeze_time("2012-01-14 12:00:00") as frozen_time:
            order_limit_group = OrderLimitGroup.objects.create(
                days_between_orders=1, name="Free Tech 6 and Below"
            )
            daily_ship = Ship.objects.create(
                name="DailyShip",
                tech_level=6,
                free=True,
                order_limit_group=order_limit_group,
            )

            self.a_ship_order(ship_pk=daily_ship.pk, payment_method="free")
            self.a_ship_order(ship_pk=daily_ship.pk, payment_method="free")

            frozen_time.move_to("2014-01-15 12:00:01")
            # Tokens expire when moving time in tests!
            self.client.force_login(self.user)
            response = self.get(reverse("industry:shiporder-list"))
            self.json_matches(
                response,
                f"""[
        {{
            "assignee": null,
                    "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
            ],
            "blocked_until": null,
            "created_at": "2012-01-14 12:00",
            "currently_blocked": false,
            "id": "IGNORE",
            "notes": "",
            "payment_method": "free",
            "quantity": 1,
            "recipient_discord_user_pk": "{self.discord_user.pk}",
            "recipient_character_name": "Test Char",
            "ship": "DailyShip",
            "state": "not_started",
            "uid": "Test Discord User-mock_random_1",
            "needs_manual_price": false,
            "payment_taken": true,
            "price": null
        }},
        {{
            "assignee": null,
                    "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
            ],
            "blocked_until": "2012-01-15 12:00",
            "created_at": "2012-01-14 12:00",
            "currently_blocked": false,
            "id": "IGNORE",
            "notes": "",
            "payment_method": "free",
            "quantity": 1,
            "recipient_discord_user_pk": "{self.discord_user.pk}",
            "recipient_character_name": "Test Char",
            "ship": "DailyShip",
            "state": "not_started",
            "uid": "Test Discord User-mock_random_2",
            "needs_manual_price": false,
            "payment_taken": true,
            "price": null
        }}
    ]""",
            )

    @freeze_time("2012-01-14 12:00:00")
    def test_ship_with_no_price_can_have_manual_price_entered(self):
        group = Group.objects.get(name="industry")
        self.user.groups.add(group)
        unpriced_ship = Ship.objects.create(
            name="ShipWithNoPrice",
            tech_level=6,
            free=True,
            isk_price=None,
            eggs_price=None,
        )

        unpriced_ship_order = self.a_ship_order(
            ship_pk=unpriced_ship.pk, payment_method="isk"
        )

        self.put(
            reverse("industry:shiporder-claim", args=[unpriced_ship_order.pk]),
        )
        self.put(
            reverse("industry:shiporder-manual-price", args=[unpriced_ship_order.pk]),
            {"manual_price": 10},
            content_type="application/json",
        )
        response = self.get(reverse("industry:shiporder-list"))
        self.json_matches(
            response,
            f"""[
        {{
            "assignee": {self.user.pk},
            "assignee_name": "{self.user.discord_username()}",
            "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
            ],
            "blocked_until": null,
            "created_at": "2012-01-14 12:00",
            "currently_blocked": false,
            "id": "IGNORE",
            "notes": "",
            "payment_method": "isk",
            "quantity": 1,
            "recipient_discord_user_pk": "{self.discord_user.pk}",
            "recipient_character_name": "Test Char",
            "ship": "ShipWithNoPrice",
            "state": "not_started",
            "uid": "Test Discord User-mock_random_1",
            "needs_manual_price": false,
            "payment_taken": false,
            "price": "10.00"
        }}]""",
        )

    @freeze_time("2012-01-14 12:00:00")
    def test_can_mark_a_ship_as_paid_for(self):
        group = Group.objects.get(name="industry")
        self.user.groups.add(group)
        unpriced_ship = Ship.objects.create(
            name="ShipWithNoPrice",
            tech_level=6,
            free=True,
            isk_price=None,
            eggs_price=None,
        )

        unpriced_ship_order = self.a_ship_order(
            ship_pk=unpriced_ship.pk, payment_method="isk"
        )

        self.put(
            reverse("industry:shiporder-claim", args=[unpriced_ship_order.pk]),
        )
        self.put(
            reverse("industry:shiporder-paid", args=[unpriced_ship_order.pk]),
            content_type="application/json",
        )
        response = self.get(reverse("industry:shiporder-list"))
        self.json_matches(
            response,
            f"""[
        {{
            "assignee": {self.user.pk},
            "assignee_name": "{self.user.discord_username()}",
            "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
            ],
            "blocked_until": null,
            "created_at": "2012-01-14 12:00",
            "currently_blocked": false,
            "id": "IGNORE",
            "notes": "",
            "payment_method": "isk",
            "quantity": 1,
            "recipient_discord_user_pk": "{self.discord_user.pk}",
            "recipient_character_name": "Test Char",
            "ship": "ShipWithNoPrice",
            "state": "not_started",
            "uid": "Test Discord User-mock_random_1",
            "needs_manual_price": false,
            "payment_taken": true,
            "price": null
        }}]""",
        )

    @freeze_time("2012-01-14 12:00:00")
    def test_ship_with_valid_price_doesnt_need_price(self):
        group = Group.objects.get(name="industry")
        self.user.groups.add(group)
        unpriced_ship = Ship.objects.create(
            name="ShipWithNoPrice",
            tech_level=6,
            free=True,
            isk_price=100,
            eggs_price=100,
            prices_last_updated=timezone.make_aware(
                timezone.datetime(2012, 1, 14, 11, 30, 0)
            ),
        )

        unpriced_ship_order = self.a_ship_order(
            ship_pk=unpriced_ship.pk, payment_method="isk", price=100
        )

        self.put(
            reverse("industry:shiporder-claim", args=[unpriced_ship_order.pk]),
        )
        self.put(
            reverse("industry:shiporder-manual-price", args=[unpriced_ship_order.pk]),
            {"manual_price": 10},
            content_type="application/json",
        )
        response = self.get(reverse("industry:shiporder-list"))
        self.json_matches(
            response,
            f"""[
        {{
            "assignee": {self.user.pk},
            "assignee_name": "{self.user.discord_username()}",
            "availible_transition_names": [
                "audit",
                "building",
                "inventing",
                "reset",
                "sent"
            ],
            "blocked_until": null,
            "created_at": "2012-01-14 12:00",
            "currently_blocked": false,
            "id": "IGNORE",
            "notes": "",
            "payment_method": "isk",
            "quantity": 1,
            "recipient_discord_user_pk": "{self.discord_user.pk}",
            "recipient_character_name": "Test Char",
            "ship": "ShipWithNoPrice",
            "state": "not_started",
            "uid": "Test Discord User-mock_random_1",
            "needs_manual_price": false,
            "payment_taken": false,
            "price": "10.00"
        }}]""",
        )

    @freeze_time("2012-01-14 12:00:00")
    def test_ship_submitting_with_old_prices_generates_error(self):
        group = Group.objects.get(name="industry")
        self.user.groups.add(group)
        unpriced_ship = Ship.objects.create(
            name="ShipWithNoPrice",
            tech_level=6,
            free=True,
            isk_price=100,
            eggs_price=100,
            prices_last_updated=timezone.make_aware(
                timezone.datetime(2012, 1, 14, 11, 30, 0)
            ),
        )

        r = self.client.post(
            reverse("industry:shiporders_create"),
            {
                "ship": unpriced_ship.pk,
                "quantity": 1,
                "recipient_character": self.char.pk,
                "payment_method": "eggs",
                "notes": "",
                "isk_price": 10,
                "eggs_price": 10,
            },
        )
        self.assert_messages(
            r,
            [
                (
                    "error",
                    "The prices for the ship have changed since you opened the order form, please order again the prices have been updated. Ƶ 100.00 vs Ƶ 10.00 and Ƶ 100.00 vs Ƶ 10.00",
                )
            ],
        )
