from decimal import Decimal
from typing import List, Optional, Union

from django.http.response import HttpResponse
from django.test import TestCase
from django.urls.base import reverse
from djmoney.money import Money

from core.models import (
    Character,
    Corp,
    DiscordUser,
    Fleet,
    FleetType,
    GooseUser,
    InventoryItem,
    Item,
    ItemFilterGroup,
    ItemLocation,
    ItemSubSubType,
    ItemSubType,
    ItemType,
    LootGroup,
    LootShare,
    MarketOrder,
    Region,
    SoldItem,
    StackedInventoryItem,
    System,
)


def isk(number_str: Union[str, int]):
    return Money(Decimal(number_str), currency="EEI")


# pylint: disable=too-many-instance-attributes
class GooseToolsTestCase(TestCase):
    def setUp(self):
        item_type = ItemType.objects.create(name="item_type")
        sub_type = ItemSubType.objects.create(name="sub_type", item_type=item_type)
        sub_sub_type = ItemSubSubType.objects.create(
            name="sub_sub_type", item_sub_type=sub_type
        )
        self.item = Item.objects.create(name="Tritanium", item_type=sub_sub_type)
        self.another_item = Item.objects.create(name="Condor", item_type=sub_sub_type)

        self.discord_user = DiscordUser.objects.create(username="Test Discord User")
        self.other_discord_user = DiscordUser.objects.create(
            username="Test Discord User 2"
        )
        self.corp = Corp.objects.create(name="Test Corp")
        self.char = Character.objects.create(
            discord_user=self.discord_user, ingame_name="Test Char", corp=self.corp
        )
        self.other_char = Character.objects.create(
            discord_user=self.other_discord_user,
            ingame_name="Test Char 2",
            corp=self.corp,
        )
        self.user = GooseUser.objects.create(
            username="Test Goose User",
            discord_user=self.discord_user,
            default_character=self.char,
        )
        self.other_user = GooseUser.objects.create(
            username="Test Goose User 2",
            discord_user=self.other_discord_user,
            default_character=self.other_char,
        )
        self.fleet_type = FleetType.objects.create(
            type="Test Fleet Type", material_icon="icon", material_colour="colour"
        )
        region = Region.objects.create(name="Test Region")
        self.system = System.objects.create(name="Test System", region=region)
        ItemFilterGroup.objects.create(name="None")
        self.client.force_login(self.user)
        self.logged_in_user = self.user

    def a_fleet(self, fleet_name="Test Fleet") -> Fleet:
        response = self.client.post(
            reverse("fleet_create"),
            {
                "start_date": "Nov. 13, 2020",
                "start_time": "01:02 PM",
                "fleet_type": self.fleet_type.id,
                "fc_character": self.char.id,
                "loot_type": "Master Looter",
                "name": fleet_name,
                "gives_shares_to_alts": False,
                "loot_was_stolen": False,
            },
        )
        self.assertEqual(response.status_code, 302)
        return Fleet.objects.get(name=fleet_name)

    def a_loot_group(self, fleet: Fleet) -> LootGroup:
        num_loot_groups_for_fleet_before = LootGroup.objects.filter(
            fleet_anom__fleet=fleet
        ).count()
        response = self.client.post(
            reverse("loot_group_create", args=[fleet.pk]),
            {
                "loot_source": "Anom",
                "anom_level": 6,
                "anom_type": "Scout",
                "anom_faction": "Serpentis",
                "anom_system": self.system.pk,
            },
        )
        num_loot_groups_for_fleet_after = LootGroup.objects.filter(
            fleet_anom__fleet=fleet
        ).count()
        self.assertEqual(
            num_loot_groups_for_fleet_after, num_loot_groups_for_fleet_before + 1
        )
        self.assertEqual(response.status_code, 302)
        # TODO Use a better way of obtaining models created by POSTing to api's.
        loot_group = LootGroup.objects.filter(fleet_anom__fleet=fleet).last()
        if loot_group is None:
            raise AssertionError("No Loot Group found in DB after making one")
        return loot_group

    def stack_items(self, loc: ItemLocation):
        response = self.client.post(reverse("stack_items", args=[loc.pk]))
        self.assertEqual(response.status_code, 302)

    def an_item(
        self, loot_group: LootGroup, item: Item = None, item_quantity: int = 1
    ) -> InventoryItem:
        if item is None:
            item = self.item
        num_items_in_loot_group_before = loot_group.inventoryitem_set.count()
        response = self.client.post(
            reverse("item_add", args=[loot_group.pk]),
            {
                "character": self.char.pk,
                "form-0-item": item.pk,
                "form-0-quantity": item_quantity,
                "form-TOTAL_FORMS": 1,
                "form-INITIAL_FORMS": 1,
            },
        )
        self.assertEqual(response.status_code, 302)
        num_items_in_loot_group_after = loot_group.inventoryitem_set.count()

        self.assertEqual(
            num_items_in_loot_group_after, num_items_in_loot_group_before + 1
        )
        created_item = loot_group.inventoryitem_set.last()
        if created_item is None:
            raise AssertionError("No item found after adding one.")
        return created_item

    def a_loot_share(
        self,
        loot_group: LootGroup,
        char: Character,
        share_quantity=1,
        flat_percent_cut=0,
    ) -> LootShare:
        response = self.client.post(
            reverse("loot_share_add", args=[loot_group.pk]),
            {
                "character": char.pk,
                "share_quantity": share_quantity,
                "flat_percent_cut": flat_percent_cut,
            },
        )
        self.assertEqual(response.status_code, 302)
        return LootShare.objects.get(
            loot_group=loot_group,
            character=char,
            share_quantity=share_quantity,
            flat_percent_cut=flat_percent_cut,
        )

    def list_stack_returning_reponse(
        self,
        stack: Optional[StackedInventoryItem],
        listed_at_price: Union[Decimal, int],
        transaction_tax: Union[Decimal, int],
        broker_fee: Union[Decimal, int],
        quantity: int = None,
    ) -> HttpResponse:
        if stack is None:
            raise AssertionError("Missing Stack")
        original_item_quantity = stack.quantity()
        if quantity is None:
            quantity = original_item_quantity
        return self.client.post(
            reverse("stack_sell", args=[stack.pk]),
            {
                "quantity": quantity,
                "transaction_tax": transaction_tax,
                "broker_fee": broker_fee,
                "listed_at_price": listed_at_price,
            },
        )

    def list_item_returning_reponse(
        self,
        item: InventoryItem,
        listed_at_price: Union[Decimal, int],
        transaction_tax: Union[Decimal, int],
        broker_fee: Union[Decimal, int],
        quantity: int = None,
    ) -> HttpResponse:
        original_item_quantity = item.quantity
        if quantity is None:
            quantity = original_item_quantity
        return self.client.post(
            reverse("item_sell", args=[item.pk]),
            {
                "quantity": quantity,
                "transaction_tax": transaction_tax,
                "broker_fee": broker_fee,
                "listed_at_price": listed_at_price,
            },
        )

    def list_item_stack(
        self,
        stack: Optional[StackedInventoryItem],
        listed_at_price: Union[Decimal, int],
        transaction_tax: Union[Decimal, int],
        broker_fee: Union[Decimal, int],
        quantity: int = None,
    ) -> List[MarketOrder]:
        if stack is None:
            raise AssertionError("Missing Stack")
        original_item_quantity = stack.quantity()
        if quantity is None:
            quantity = original_item_quantity
        stack_a = StackedInventoryItem.objects.last()
        response = self.list_stack_returning_reponse(
            stack, listed_at_price, transaction_tax, broker_fee, quantity
        )
        stack_b = StackedInventoryItem.objects.last()
        if stack_a is None or stack_b is None:
            raise AssertionError("Failed to find before and after stacks")
        if stack_a != stack_b:
            new_stack = stack_b
        else:
            new_stack = stack
        self.assertEqual(response.status_code, 302)

        market_orders = MarketOrder.objects.filter(item__stack=new_stack).all()
        if new_stack != stack:
            self.assertEqual(stack.quantity(), original_item_quantity - quantity)
            self.assertEqual(stack.order_quantity(), 0)
        self.assertEqual(new_stack.quantity(), 0)
        self.assertEqual(new_stack.order_quantity(), quantity)
        return market_orders  # type: ignore

    def list_item(
        self,
        item: InventoryItem,
        listed_at_price: Union[Decimal, int],
        transaction_tax: Union[Decimal, int],
        broker_fee: Union[Decimal, int],
        quantity: int = None,
    ) -> MarketOrder:
        original_item_quantity = item.quantity
        if quantity is None:
            quantity = original_item_quantity
        response = self.list_item_returning_reponse(
            item, listed_at_price, transaction_tax, broker_fee, quantity
        )
        self.assertEqual(response.status_code, 302)

        if item.quantity == quantity:
            # We aren't listing a sub quantity so the item wont be split
            market_order = MarketOrder.objects.get(item=item)
        else:
            # We listed a sub quantity so a new item was split off and used to make the market order, search for it this way.
            market_order = MarketOrder.objects.get(
                item__item=item.item, quantity=quantity
            )

        item.refresh_from_db()
        self.assertEqual(item.quantity, original_item_quantity - quantity)
        self.assertEqual(market_order.quantity, quantity)
        return market_order

    def change_market_order_price(
        self,
        market_order: MarketOrder,
        new_price: Union[Decimal, int],
        broker_fee: Union[Decimal, int],
    ):
        response = self.client.post(
            reverse("edit_order_price", args=[market_order.pk]),
            {
                "new_price": new_price,
                "broker_fee": broker_fee,
            },
        )
        self.assertEqual(response.status_code, 302)

    def stack_market_order_sold(self, stack: Optional[StackedInventoryItem]) -> None:
        if stack is None:
            raise AssertionError("Missing stack")

        response = self.client.post(
            reverse("stack_sold", args=[stack.pk]),
            {"quantity_remaining": 0},
        )
        self.assertEqual(response.status_code, 302)

    def market_order_sold(
        self, market_order: MarketOrder, quantity_remaining: int = 0
    ) -> SoldItem:
        response = self.client.post(
            reverse("order_sold", args=[market_order.pk]),
            {"quantity_remaining": quantity_remaining},
        )
        self.assertEqual(response.status_code, 302)
        if quantity_remaining == 0:
            self.assertEqual(
                MarketOrder.objects.filter(item=market_order.item).count(), 0
            )
        else:
            market_order.refresh_from_db()
            self.assertEqual(market_order.quantity, quantity_remaining)
        sold_item = SoldItem.objects.get(item=market_order.item)
        return sold_item
