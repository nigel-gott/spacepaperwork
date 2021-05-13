from allauth.socialaccount.models import SocialAccount
from django.contrib.messages import get_messages
from django.urls.base import reverse

from goosetools.ownership.models import TransferLog
from goosetools.tenants.models import SiteUser
from goosetools.tests.goosetools_test_case import GooseToolsTestCase, isk
from goosetools.users.models import LOOT_TRACKER, Character, GooseGroup, GooseUser


class MarketOrderTestCase(GooseToolsTestCase):
    def setUp(self):
        super().setUp()
        loot_tracker_group, _ = GooseGroup.objects.get_or_create(name="loot_tracker")
        loot_tracker_group.link_permission(LOOT_TRACKER)
        self.user.give_group(loot_tracker_group)
        self.other_user.give_group(loot_tracker_group)

    def test_anom_loot_when_only_the_seller_has_a_share_and_wants_it_in_isk(self):
        # Given there is a basic fleet with a single item split between two different people:
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=1)

        self.a_loot_share(loot_group, self.char, share_quantity=1, flat_percent_cut=5)

        # When the item gets sold and the profit transfered
        market_order = self.list_item(
            item, listed_at_price=10000, transaction_tax=10, broker_fee=5
        )
        sold_item = self.market_order_sold(market_order)

        self.assertEqual(self.user.isk_balance(), isk(8500))
        self.assertEqual(self.user.egg_balance(), isk(0))
        self.assertEqual(sold_item.transfered_so_far(), False)

        response = self.client.post(
            reverse("transfer_profit"),
            {"own_share_in_eggs": False, "transfer_method": "eggs"},
        )
        self.assertEqual(response.status_code, 302)

        sold_item.refresh_from_db()
        self.assertEqual(sold_item.transfered_so_far(), True)
        self.assertEqual(self.user.isk_balance(), isk("0"))
        self.assertEqual(self.user.egg_balance(), isk("8500"))
        log = TransferLog.objects.all()[0]
        self.assertEqual(log.deposit_command, "$deposit 0")
        self.assertEqual(log.transfer_command, "no one to transfer to")

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

        self.assertEqual(self.user.isk_balance(), isk(8500))
        self.assertEqual(self.user.egg_balance(), isk(0))
        self.assertEqual(sold_item.transfered_so_far(), False)

        response = self.client.post(
            reverse("transfer_profit"),
            {"own_share_in_eggs": True, "transfer_method": "eggs"},
        )
        self.assertEqual(response.status_code, 302)

        # Then the sold_item is marked as transfered and the correct deposit and transfer commands are generated based off the items profit and loot_group participation:
        #   We Sold an item for 10,000 ISK @ 15% market fees so Z 8500 profit.
        #   Then the selling using self.char gets a 5% cut of that profit which is Z 425 leaving Z 8075 to be split by shares after.
        #   Both characters have 1 share so each gets 1*8075/2 = Z 4037.5
        #   Adding self.char's 1 share and flat % cut gets 4462.5.
        #   All egg quantitys are floored, however the seller gets any fractional remains hence self.char ends up with 4462 + 1 = Z 4463.
        sold_item.refresh_from_db()
        self.assertEqual(sold_item.transfered_so_far(), True)
        self.assertEqual(self.user.isk_balance(), isk("0"))
        self.assertEqual(self.user.egg_balance(), isk("4463"))
        self.assertEqual(self.other_user.egg_balance(), isk("4037"))
        log = TransferLog.objects.all()[0]
        # The seller indicated they wanted their own share in eggs so the deposit command includes all profit.
        self.assertEqual(log.deposit_command, "$deposit 8500")
        self.assertEqual(log.transfer_command, "$bulk\n<@2> 4037\n")
        # The seller can later mark the transfer as all done
        # However this is just a graphical display indicator to help sellers track which transfers have been completed, and has no impact on internal balances.
        self.assertEqual(log.all_done, False)

    def test_transfer_command_is_split_by_discord_character_limit(self):
        # Given there is a basic fleet with a single item split between two different people:
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=1)

        num_users = 200
        for i in range(0, num_users):
            username = f"Test Goose User - {i}"
            s = SiteUser.create(username)
            user = GooseUser.objects.create(
                site_user=s,
                status="approved",
            )
            char = Character.objects.create(
                user=user,
                ingame_name=f"A Test Char {i:02d}",
                corp=self.corp,
            )
            SocialAccount.objects.create(
                uid=i + 10,
                provider="discord",
                extra_data={
                    "username": username,
                    "discriminator": "1",
                },
                user_id=s.pk,
            )
            user.cache_fields_from_social_account()
            self.a_loot_share(loot_group, char, share_quantity=1)

        # When the item gets sold and the profit transfered
        market_order = self.list_item(
            item, listed_at_price=10000, transaction_tax=10, broker_fee=5
        )
        sold_item = self.market_order_sold(market_order)

        self.assertEqual(self.user.isk_balance(), isk(8500))
        self.assertEqual(self.user.egg_balance(), isk(0))
        self.assertEqual(sold_item.transfered_so_far(), False)

        response = self.client.post(
            reverse("transfer_profit"),
            {"own_share_in_eggs": True, "transfer_method": "eggs"},
        )
        self.assertEqual(response.status_code, 302)

        sold_item.refresh_from_db()
        self.assertEqual(sold_item.transfered_so_far(), True)
        self.assertEqual(self.user.isk_balance(), isk("0"))
        self.assertEqual(self.user.egg_balance(), isk("100"))
        log = TransferLog.objects.all()[0]
        # The seller indicated they wanted their own share in eggs so the deposit command includes all profit.
        self.assertEqual(log.deposit_command, "$deposit 8500")
        self.assertIn(
            "NEW MESSAGE TO AVOID DISCORD CHARACTER LIMIT", log.transfer_command
        )
        # The seller can later mark the transfer as all done
        # However this is just a graphical display indicator to help sellers track which transfers have been completed, and has no impact on internal balances.
        self.assertEqual(log.all_done, False)

    def test_loot_transfer_doesnt_deposit_sellers_share_if_they_want_to_keep_it_in_isk(
        self,
    ):
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

        self.assertEqual(self.user.isk_balance(), isk(8500))
        self.assertEqual(self.user.egg_balance(), isk(0))
        self.assertEqual(sold_item.transfered_so_far(), False)

        response = self.client.post(
            reverse("transfer_profit"),
            {"own_share_in_eggs": False, "transfer_method": "eggs"},
        )
        self.assertEqual(response.status_code, 302)

        # Then the sold_item is marked as transfered and the correct deposit and transfer commands are generated based off the items profit and loot_group participation:
        #   We Sold an item for 10,000 ISK @ 15% market fees so Z 8500 profit.
        #   Then the selling using self.char gets a 5% cut of that profit which is Z 425 leaving Z 8075 to be split by shares after.
        #   Both characters have 1 share so each gets 1*8075/2 = Z 4037.5
        #   Adding self.char's 1 share and flat % cut gets 4462.5.
        #   All egg quantitys are floored, however the seller gets any fractional remains hence self.char ends up with 4462 + 1 = Z 4463.
        sold_item.refresh_from_db()
        self.assertEqual(sold_item.transfered_so_far(), True)
        self.assertEqual(self.user.isk_balance(), isk("0"))
        self.assertEqual(self.user.egg_balance(), isk("4463"))
        self.assertEqual(self.other_user.egg_balance(), isk("4037"))
        log = TransferLog.objects.all()[0]
        # The seller indicated they wanted their own share in isk so the deposit command only includes the other players shares.
        self.assertEqual(log.deposit_command, "$deposit 4037")
        self.assertEqual(log.transfer_command, "$bulk\n<@2> 4037\n")
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

        self.assertEqual(self.user.isk_balance(), isk(8500))
        self.assertEqual(self.user.egg_balance(), isk(0))
        self.assertEqual(sold_item.transfered_so_far(), False)

        response = self.client.post(
            reverse("transfer_profit"),
            {"own_share_in_eggs": False, "transfer_method": "eggs"},
        )
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            len(messages),
            2,
            f"Expecting only two messages instead got: {[str(message) for message in messages]}",
        )
        self.assertEqual(
            str(messages[0]),
            "Sold 1 of item Tritanium x 2 @ Space On Test Char(Test Goose User)",
        )
        self.assertIn(
            "The following loot groups you are attempting to transfer isk for have no participation at all",
            str(messages[1]),
        )

        # The item fails to be transfered as there is no participation for it
        self.assertEqual(self.user.isk_balance(), isk(8500))
        self.assertEqual(self.user.egg_balance(), isk(0))
        self.assertEqual(sold_item.transfered_so_far(), False)

    def test_egg_transfer_fails_if_one_item_has_negative_profit(self):
        # Given there is a basic fleet with a two items
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=1)
        another_item = self.an_item(loot_group, item=self.another_item, item_quantity=2)

        self.a_loot_share(loot_group, self.char, share_quantity=1, flat_percent_cut=5)
        self.a_loot_share(loot_group, self.other_char, share_quantity=1)

        # When the first item gets sold for a profit
        market_order = self.list_item(
            item, listed_at_price=10000, transaction_tax=10, broker_fee=5
        )
        sold_item = self.market_order_sold(market_order)
        # However the second item looses money as the price is lowered to something below the fees incurred.
        # Incurs a total broker fee of 5000*2*0.05 = Z 500
        another_market_order = self.list_item(
            another_item, listed_at_price=5000, transaction_tax=10, broker_fee=5
        )
        self.change_market_order_price(another_market_order, new_price=1, broker_fee=5)
        # Sells for Z 2 resulting in a Z -498 profit
        another_sold_item = self.market_order_sold(another_market_order)

        self.assertEqual(another_item.isk_balance(), isk(-498))
        self.assertEqual(self.user.isk_balance(), isk(8002))
        self.assertEqual(self.user.egg_balance(), isk(0))
        self.assertEqual(sold_item.transfered_so_far(), False)
        self.assertEqual(another_sold_item.transfered_so_far(), False)

        response = self.client.post(
            reverse("transfer_profit"),
            {"own_share_in_eggs": False, "transfer_method": "eggs"},
        )
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            len(messages),
            4,
            f"Expecting only four messages instead got: {[str(message) for message in messages]}",
        )
        self.assertEqual(
            str(messages[0]),
            "Sold 1 of item Tritanium x 2 @ Space On Test Char(Test Goose User)",
        )
        self.assertIn("Market Price Was Reduced from 5000.00 to 1", str(messages[1]))
        self.assertEqual(
            str(messages[2]),
            "Sold 2 of item Condor x 4 @ Space On Test Char(Test Goose User)",
        )
        self.assertIn(
            "You are trying to transfer an item which has made a negative profit",
            str(messages[3]),
        )

        # Both items fail to be transfered as one has made a negative profit and an admin needs to do something about it
        self.assertEqual(self.user.isk_balance(), isk(8002))
        self.assertEqual(self.user.egg_balance(), isk(0))
        self.assertEqual(sold_item.transfered_so_far(), False)
        self.assertEqual(another_sold_item.transfered_so_far(), False)

    def test_transfering_an_item_multiple_times_as_it_sells_one_by_one_works(self):
        # Given there is a basic fleet with a two items
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=10)

        self.a_loot_share(loot_group, self.char, share_quantity=1, flat_percent_cut=5)
        self.a_loot_share(loot_group, self.other_char, share_quantity=1)

        # When the first item gets sold for a profit
        market_order = self.list_item(
            item, listed_at_price=10000, transaction_tax=10, broker_fee=5
        )
        # Only half the order sells
        sold_item = self.market_order_sold(market_order, quantity_remaining=5)

        # Half has sold, the other half has an outstanding 5% broker fee.
        self.assertEqual(self.user.isk_balance(), isk(8500 * 5 - 5 * 500))
        self.assertEqual(self.user.egg_balance(), isk(0))
        self.assertEqual(sold_item.transfered_so_far(), False)

        # We transfer only that half sold so far
        response = self.client.post(
            reverse("transfer_profit"),
            {"own_share_in_eggs": False, "transfer_method": "eggs"},
        )
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            len(messages),
            2,
            f"Expecting only two messages instead got: {[str(message) for message in messages]}",
        )
        self.assertEqual(
            str(messages[0]),
            "Sold 5 of item Tritanium x 10 @ Space On Test Char(Test Goose User)",
        )
        self.assertEqual(
            "Generated Deposit and Transfer commands for Ƶ 40,000.00 eggs from 5 sold items!.",
            str(messages[1]),
        )

        self.assertEqual(self.user.isk_balance(), isk(0))
        self.assertEqual(self.user.egg_balance(), isk(21000))
        self.assertEqual(self.other_user.egg_balance(), isk(19000))

        # We sell the other half after a transfer
        market_order.refresh_from_db()
        self.market_order_sold(market_order, quantity_remaining=0)

        # The first transfer also included the negative broker fee for all items in the stack hence not including it in this balance.
        self.assertEqual(self.user.isk_balance(), isk(9000 * 5))

        # We transfer The other half
        response = self.client.post(
            reverse("transfer_profit"),
            {"own_share_in_eggs": False, "transfer_method": "eggs"},
        )

        self.assertEqual(self.user.isk_balance(), isk(0))
        self.assertEqual(self.user.egg_balance(), isk(44625))
        self.assertEqual(self.other_user.egg_balance(), isk(40375))
