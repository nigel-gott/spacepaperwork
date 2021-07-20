from decimal import Decimal
from typing import List, Optional, Union

from allauth.socialaccount.models import SocialAccount
from django.http.response import HttpResponse
from django.urls.base import reverse
from djmoney.money import Money

from goosetools.core.models import Region
from goosetools.fleets.models import Fleet
from goosetools.items.models import (
    InventoryItem,
    Item,
    ItemLocation,
    ItemSubSubType,
    ItemSubType,
    ItemType,
    StackedInventoryItem,
    System,
)
from goosetools.market.models import MarketOrder, SoldItem
from goosetools.ownership.models import LootGroup, LootShare
from goosetools.tenants.models import SiteUser
from goosetools.tests.django_test_case import DjangoTestCase
from goosetools.users.models import (
    BASIC_ACCESS,
    LOOT_TRACKER,
    USER_ADMIN_PERMISSION,
    Character,
    Corp,
    GooseGroup,
    GoosePermission,
    GooseUser,
)


def isk(number_str: Union[str, int]):
    return Money(Decimal(number_str), currency="EEI")


# pylint: disable=too-many-instance-attributes
class GooseToolsTestCase(DjangoTestCase):
    def setUp(self):
        super().setUp()
        item_type = ItemType.objects.create(name="item_type")
        sub_type = ItemSubType.objects.create(name="sub_type", item_type=item_type)
        sub_sub_type = ItemSubSubType.objects.create(
            name="sub_sub_type", item_sub_type=sub_type
        )
        self.item = Item.objects.create(name="Tritanium", item_type=sub_sub_type)
        self.another_item = Item.objects.create(name="Condor", item_type=sub_sub_type)

        self.corp = Corp.objects.create(name="Test Corp")
        self.site_user = SiteUser.create("Test Goose User#1234")
        self.basic_access_group = GooseGroup.objects.create(name="basic_access")
        self.basic_access_group.link_permission(BASIC_ACCESS)
        self.basic_access_group.link_permission(LOOT_TRACKER)
        self.user_admin_group = GooseGroup.objects.create(name="user_admin_group")
        self.user_admin_group.link_permission(USER_ADMIN_PERMISSION)
        self.user = GooseUser.objects.create(
            site_user=self.site_user,
            status="approved",
        )
        self.user.give_group(self.basic_access_group)
        self.char = Character.objects.create(
            user=self.user, ingame_name="Test Char", corp=self.corp
        )
        self.user_socialaccount = SocialAccount.objects.create(
            uid="1",
            provider="discord",
            extra_data={
                "username": "Test Goose User",
                "nick": "Test Goose User",
                "discriminator": "1234",
            },
            user=self.site_user,
        )
        self.other_site_user = SiteUser.create("Test Goose User 2#1234")
        self.other_user = GooseUser.objects.create(
            site_user=self.other_site_user,
            status="approved",
        )
        self.other_user.give_group(self.basic_access_group)
        self.otheruser_socialaccount = SocialAccount.objects.create(
            uid="2",
            provider="discord",
            extra_data={
                "username": "Test Goose User 2",
                "nick": "Test Goose User 2",
                "discriminator": "1234",
            },
            user=self.other_site_user,
        )
        self.other_char = Character.objects.create(
            user=self.other_user,
            ingame_name="Test Char 2",
            corp=self.corp,
        )
        self.other_alt_char = Character.objects.create(
            user=self.other_user,
            ingame_name="Test Alt Char 2",
            corp=self.corp,
        )
        region = Region.objects.create(name="Test Region")
        self.system = System.objects.create(name="Test System", region=region)
        self.client.force_login(self.site_user)
        self.logged_in_user = self.user
        self.user.cache_fields_from_social_account()
        self.other_user.cache_fields_from_social_account()

    def a_fleet(
        self,
        fleet_name="Test Fleet",
        start_date="Nov. 13, 2020",
        start_time="01:02 PM",
        end_date=None,
        end_time=None,
        gives_shares_to_alts=False,
    ) -> Fleet:
        args = {
            "start_date": start_date,
            "start_time": start_time,
            "fc_character": self.char.id,
            "loot_type": "Master Looter",
            "name": fleet_name,
            "gives_shares_to_alts": gives_shares_to_alts,
            "form-TOTAL_FORMS": 2,
            "form-INITIAL_FORMS": 2,
            "form-0-control": "view",
            "form-0-allow_or_deny": "allow",
            "form-0-existing_entity": "",
            "form-0-permission": GoosePermission.objects.get(name=BASIC_ACCESS).id,
            "form-0-corp": "",
            "form-0-user": "",
            "form-0-DELETE": "",
            "form-1-control": "use",
            "form-1-allow_or_deny": "allow",
            "form-1-existing_entity": "",
            "form-1-permission": GoosePermission.objects.get(name=BASIC_ACCESS).id,
            "form-1-corp": "",
            "form-1-user": "",
            "form-1-DELETE": "",
        }
        if end_date:
            args["end_date"] = end_date
            args["end_time"] = end_time
        response = self.post(reverse("fleet_create"), args)
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
