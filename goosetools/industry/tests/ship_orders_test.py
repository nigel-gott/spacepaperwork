from django.contrib.auth.models import Group
from django.urls.base import reverse
from freezegun import freeze_time

from goosetools import industry
from goosetools.industry.models import Ship, ShipOrder
from goosetools.tests.goosetools_test_case import GooseToolsTestCase


# TODO Figure out a better way of mocking this out rather than monkey
def get_mock_random_string():
    return "mock_random"


industry.views.generate_random_string = get_mock_random_string


@freeze_time("2012-01-14 12:00:00")
class ShipOrderTest(GooseToolsTestCase):
    def setUp(self):
        super().setUp()
        self.thorax = Ship.objects.create(name="Thorax", tech_level=6)

    def a_ship_order_returning_response(self, ship_pk=None, payment_method="eggs"):
        if not ship_pk:
            ship_pk = self.thorax.pk
        r = self.post(
            reverse("industry:shiporders_create"),
            {
                "ship": ship_pk,
                "quantity": 1,
                "recipient_character": self.char.pk,
                "payment_method": payment_method,
                "notes": "",
            },
        )
        ship_order = ShipOrder.objects.last()
        self.post(reverse("industry:shiporders_contract_confirm", args=[ship_order.pk]))
        return r

    def a_ship_order(self, ship_pk=None, payment_method="eggs"):
        self.a_ship_order_returning_response(ship_pk, payment_method)
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
        self.assertEqual(
            str(response.content, encoding="utf-8"),
            f'{{"id":{ship_order.id},"uid":"Test Discord User-mock_random","created_at":"2012-01-14 12:00","ship":"Thorax","quantity":1,"assignee":null,"recipient_character":{self.char.pk},"payment_method":"eggs","state":"not_started","notes":"","recipient_character_name":"{self.char.ingame_name}","availible_transition_names":["building","built","inventing","reset"]}}',
        )

    def test_can_list_ship_orders(self):
        ship_order = self.a_ship_order()
        response = self.get(reverse("industry:shiporder-list"))
        self.assertEqual(
            str(response.content, encoding="utf-8"),
            f'[{{"id":{ship_order.id},"uid":"Test Discord User-mock_random","created_at":"2012-01-14 12:00","ship":"Thorax","quantity":1,"assignee":null,"recipient_character":{self.char.pk},"payment_method":"eggs","state":"not_started","notes":"","recipient_character_name":"{self.char.ingame_name}","availible_transition_names":["building","built","inventing","reset"]}}]',
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
        self.assertEqual(
            str(response.content, encoding="utf-8"),
            f'[{{"id":{ship_order.id},"uid":"Test Discord User-mock_random","created_at":"2012-01-14 12:00","ship":"Thorax","quantity":1,"assignee":{self.user.pk},"recipient_character":{self.char.pk},"payment_method":"eggs","state":"not_started","notes":"","recipient_character_name":"{self.char.ingame_name}","assignee_name":"{self.user.discord_username()}","availible_transition_names":["building","built","inventing","reset"]}}]',
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
            "building",
            "built",
            "inventing",
            "reset"
        ],
        "created_at": "2012-01-14 12:00",
        "id": {ship_order.pk},
        "notes": "",
        "payment_method": "free",
        "quantity": 1,
        "recipient_discord_user_pk": {self.discord_user.pk},
        "recipient_character_name": "Test Char",
        "ship": "FreeShip",
        "state": "not_started",
        "uid": "Test Discord User-mock_random"
    }}
]""",
        )

    def test_ordering_a_free_ship_with_isk_turns_the_method_into_free(self):
        free_ship = Ship.objects.create(name="FreeShip", tech_level=6, free=True)
        r = self.a_ship_order_returning_response(free_ship.pk, payment_method="isk")

        self.assert_messages(
            r,
            [
                (
                    "info",
                    "This ship is free, you selected to pay with isk, instead this has been switched to free!",
                )
            ],
        )

        r = self.get(reverse("industry:shiporder-list"))
        self.json_matches(
            r,
            f"""[
     {{
        "assignee": null,
        "availible_transition_names": [
            "building",
            "built",
            "inventing",
            "reset"
        ],
        "created_at": "2012-01-14 12:00",
        "id": {ShipOrder.objects.last().pk},
        "notes": "",
        "payment_method": "free",
        "quantity": 1,
        "recipient_character": {self.char.pk},
        "recipient_character_name": "Test Char",
        "ship": "FreeShip",
        "state": "not_started",
        "uid": "Test Discord User-mock_random"
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
