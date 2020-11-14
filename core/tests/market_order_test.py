from django.test import TestCase
from django.urls.base import reverse
from django.utils import timezone
from core.models import *
from django.test import Client
from django.contrib.messages import get_messages


class MarketOrderTestCase(TestCase):
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
        corp = Corp.objects.create(name="Test Corp")
        self.char = Character.objects.create(
            discord_user=self.discord_user, ingame_name="Test Char", corp=corp
        )
        self.other_char = Character.objects.create(
            discord_user=self.other_discord_user, ingame_name="Test Char 2", corp=corp
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
        return LootGroup.objects.filter(fleet_anom__fleet=fleet).last()

    def an_item(self, loot_group: LootGroup, item:Item= None, item_quantity: int = 1) -> InventoryItem:
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
        return loot_group.inventoryitem_set.last()

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

    def list_item(
        self,
        item: InventoryItem,
        listed_at_price: Decimal,
        transaction_tax: Decimal,
        broker_fee: Decimal,
    ) -> MarketOrder:
        original_item_quantity = item.quantity
        response = self.client.post(
            reverse("item_sell", args=[item.pk]),
            {
                "transaction_tax": transaction_tax,
                "broker_fee": broker_fee,
                "listed_at_price": listed_at_price,
            },
        )
        self.assertEqual(response.status_code, 302)

        market_order = MarketOrder.objects.get(item=item)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 0)
        self.assertEqual(market_order.quantity, original_item_quantity)
        return market_order
    
    def change_market_order_price(self, market_order:MarketOrder, new_price:Decimal, broker_fee:Decimal):
        response = self.client.post(
            reverse("edit_order_price", args=[market_order.pk]),
            {
                "new_price": new_price,
                "broker_fee": broker_fee,
            },
        )
        self.assertEqual(response.status_code, 302)

    def market_order_sold(self, market_order: MarketOrder) -> SoldItem:
        original_market_order_quantity = market_order.quantity
        response = self.client.post(
            reverse("order_sold", args=[market_order.pk]), {"quantity_remaining": 0}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MarketOrder.objects.filter(item=market_order.item).count(), 0)
        sold_item = SoldItem.objects.get(item=market_order.item)
        self.assertEqual(sold_item.quantity, original_market_order_quantity)
        return sold_item

    def isk(self, decimal_string: str) -> Money:
        return Money(amount=Decimal(decimal_string), currency="EEI")

    def test_anom_loot_gets_split_correctly_between_two_people_when_sold(self):
        # Given there is a basic fleet with a single item split between two different people:
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=1)

        self.a_loot_share(loot_group, self.char, share_quantity=1, flat_percent_cut=5)
        self.a_loot_share(loot_group, self.other_char, share_quantity=1)

        # When the item gets sold and the profit transfered
        market_order = self.list_item(
            item, listed_at_price=10000, transaction_tax=10, broker_fee=5
        )
        sold_item = self.market_order_sold(market_order)

        self.assertEqual(self.user.isk_balance(), to_isk(8500))
        self.assertEqual(self.user.egg_balance(), to_isk(0))
        self.assertEqual(sold_item.transfered, False)

        response = self.client.post(
            reverse("transfer_eggs"), {"own_share_in_eggs": True}
        )
        self.assertEqual(response.status_code, 302)

        # Then the sold_item is marked as transfered and the correct deposit and transfer commands are generated based off the items profit and loot_group participation:
        #   We Sold an item for 10,000 ISK @ 15% market fees so Z 8500 profit.
        #   Then the selling using self.char gets a 5% cut of that profit which is Z 425 leaving Z 8075 to be split by shares after.
        #   Both characters have 1 share so each gets 1*8075/2 = Z 4037.5
        #   Adding self.char's 1 share and flat % cut gets 4462.5.
        #   All egg quantitys are floored, however the seller gets any fractional remains hence self.char ends up with 4462 + 1 = Z 4463.
        sold_item.refresh_from_db()
        self.assertEqual(sold_item.transfered, True)
        self.assertEqual(self.user.isk_balance(), self.isk("0"))
        self.assertEqual(self.user.egg_balance(), self.isk("4463"))
        self.assertEqual(self.other_user.egg_balance(), self.isk("4037"))
        log = TransferLog.objects.all()[0]
        # The seller indicated they wanted their own share in eggs so the deposit command includes all profit.
        self.assertEqual(log.deposit_command, "$deposit 8500")
        self.assertEqual(log.transfer_command, "$bulk\n@Test Discord User 2 4037\n")
        # The seller can later mark the transfer as all done
        # However this is just a graphical display indicator to help sellers track which transfers have been completed, and has no impact on internal balances.
        self.assertEqual(log.all_done, False)

    def test_loot_transfer_doesnt_deposit_sellers_share_if_they_want_to_keep_it_in_isk(self):
        # Given there is a basic fleet with a single item split between two different people:
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=1)

        self.a_loot_share(loot_group, self.char, share_quantity=1, flat_percent_cut=5)
        self.a_loot_share(loot_group, self.other_char, share_quantity=1)

        # When the item gets sold and the profit transfered however with the seller keeping their share in eggs
        market_order = self.list_item(
            item, listed_at_price=10000, transaction_tax=10, broker_fee=5
        )
        sold_item = self.market_order_sold(market_order)

        self.assertEqual(self.user.isk_balance(), to_isk(8500))
        self.assertEqual(self.user.egg_balance(), to_isk(0))
        self.assertEqual(sold_item.transfered, False)

        response = self.client.post(
            reverse("transfer_eggs"), {"own_share_in_eggs": False}
        )
        self.assertEqual(response.status_code, 302)

        # Then the sold_item is marked as transfered and the correct deposit and transfer commands are generated based off the items profit and loot_group participation:
        #   We Sold an item for 10,000 ISK @ 15% market fees so Z 8500 profit.
        #   Then the selling using self.char gets a 5% cut of that profit which is Z 425 leaving Z 8075 to be split by shares after.
        #   Both characters have 1 share so each gets 1*8075/2 = Z 4037.5
        #   Adding self.char's 1 share and flat % cut gets 4462.5.
        #   All egg quantitys are floored, however the seller gets any fractional remains hence self.char ends up with 4462 + 1 = Z 4463.
        sold_item.refresh_from_db()
        self.assertEqual(sold_item.transfered, True)
        self.assertEqual(self.user.isk_balance(), self.isk("0"))
        self.assertEqual(self.user.egg_balance(), self.isk("4463"))
        self.assertEqual(self.other_user.egg_balance(), self.isk("4037"))
        log = TransferLog.objects.all()[0]
        # The seller indicated they wanted their own share in isk so the deposit command only includes the other players shares.
        self.assertEqual(log.deposit_command, "$deposit 4037")
        self.assertEqual(log.transfer_command, "$bulk\n@Test Discord User 2 4037\n")
        # The seller can later mark the transfer as all done
        # However this is just a graphical display indicator to help sellers track which transfers have been completed, and has no impact on internal balances.
        self.assertEqual(log.all_done, False)
    
    def test_egg_transfer_fails_if_no_participation(self):
        # Given there is a basic fleet with a single item however without any participation 
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=1)

        # When the item gets sold and the profit transfered however with the seller keeping their share in eggs
        market_order = self.list_item(
            item, listed_at_price=10000, transaction_tax=10, broker_fee=5
        )
        sold_item = self.market_order_sold(market_order)

        self.assertEqual(self.user.isk_balance(), to_isk(8500))
        self.assertEqual(self.user.egg_balance(), to_isk(0))
        self.assertEqual(sold_item.transfered, False)

        response = self.client.post(
            reverse("transfer_eggs"), {"own_share_in_eggs": False}
        )
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 2, f"Expecting only two messages instead got: {[str(message) for message in messages]}")
        self.assertEqual(str(messages[0]), "Sold 1 of item Tritanium x 2 @ Space On Test Char(Test Discord User)")
        self.assertIn("The following loot groups you are attempting to transfer isk for have no participation at all", str(messages[1]))

        # The item fails to be transfered as there is no participation for it
        self.assertEqual(self.user.isk_balance(), to_isk(8500))
        self.assertEqual(self.user.egg_balance(), to_isk(0))
        self.assertEqual(sold_item.transfered, False)