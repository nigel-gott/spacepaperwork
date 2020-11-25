from django.urls.base import reverse
from freezegun import freeze_time

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

    def test_can_order_a_ship_and_have_it_show_as_not_started_on_orders_board(self):

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

        ship_orders = self.get(reverse("industry:shiporders_view"))

        self.assertEqual(
            ship_orders.context["ship_orders"],
            [
                {
                    "created_at": "2012-01-14 12:00:00",
                    "ship": self.thorax.pk,
                    "quantity": 1,
                    "recipient_character": self.char.ingame_name,
                    "payment_method": "eggs",
                    "state": "not_started",
                    "assignee": "Nobody",
                }
            ],
        )
