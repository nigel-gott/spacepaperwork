from django.contrib.auth.models import Group
from django.urls.base import reverse
from freezegun import freeze_time

from goosetools.industry.models import ShipOrder
from goosetools.items.models import Item, ItemSubSubType, ItemSubType, ItemType
from goosetools.tests.goosetools_test_case import GooseToolsTestCase


@freeze_time("2012-01-14 12:00:00")
class ShipOrderTest(GooseToolsTestCase):
    def setUp(self):
        super().setUp()
        self.ship_type = ItemType.objects.create(name="Ships")
        self.cruiser_type = ItemSubType.objects.create(
            name="Cruisers", item_type=self.ship_type
        )
        self.cruiser_sub_type = ItemSubSubType.objects.create(
            name="Cruisers", item_sub_type=self.cruiser_type
        )
        self.thorax = Item.objects.create(
            name="Thorax", item_type=self.cruiser_sub_type
        )

    def a_ship_order(self):
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
        return ShipOrder.objects.last()

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
            f'{{"id":{ship_order.id},"created_at":"2012-01-14 12:00","ship":"Thorax","quantity":1,"assignee":null,"recipient_character":{self.char.pk},"payment_method":"eggs","state":"not_started","notes":"","recipient_character_name":"{self.char.ingame_name}"}}',
        )

    def test_can_list_ship_orders(self):
        ship_order = self.a_ship_order()
        response = self.get(reverse("industry:shiporder-list"))
        self.assertEqual(
            str(response.content, encoding="utf-8"),
            f'[{{"id":{ship_order.id},"created_at":"2012-01-14 12:00","ship":"Thorax","quantity":1,"assignee":null,"recipient_character":{self.char.pk},"payment_method":"eggs","state":"not_started","notes":"","recipient_character_name":"{self.char.ingame_name}"}}]',
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
            f'[{{"id":{ship_order.id},"created_at":"2012-01-14 12:00","ship":"Thorax","quantity":1,"assignee":{self.user.pk},"recipient_character":{self.char.pk},"payment_method":"eggs","state":"not_started","notes":"","recipient_character_name":"{self.char.ingame_name}","assignee_name":"{self.user.discord_username()}"}}]',
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
