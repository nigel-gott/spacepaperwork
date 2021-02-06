from goosetools.items.models import StackedInventoryItem
from goosetools.tests.goosetools_test_case import GooseToolsTestCase, isk
from goosetools.users.models import LOOT_TRACKER, GooseGroup


class MarketOrderTestCase(GooseToolsTestCase):
    def setUp(self):
        super().setUp()
        loot_tracker_group, _ = GooseGroup.objects.get_or_create(name="loot_tracker")
        loot_tracker_group.link_permission(LOOT_TRACKER)
        self.user.give_group(loot_tracker_group)
        self.other_user.give_group(loot_tracker_group)

    def test_cant_list_a_zero_quantity(self):
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=10)
        response = self.list_item_returning_reponse(
            item, quantity=0, listed_at_price=10000, transaction_tax=10, broker_fee=5
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Ensure this value is greater than or equal to 1.", str(response.content)
        )
        self.assertEqual(item.sold_quantity(), 0)

    def test_cant_list_a_quantity_greater_than_item_quantity(self):
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=10)
        response = self.list_item_returning_reponse(
            item,
            quantity=item.quantity + 1,
            listed_at_price=10000,
            transaction_tax=10,
            broker_fee=5,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Ensure this value is less than or equal to 10.", str(response.content)
        )
        self.assertEqual(item.sold_quantity(), 0)

    def test_cant_list_a_negative_quantity(self):
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=10)
        response = self.list_item_returning_reponse(
            item, quantity=-1, listed_at_price=10000, transaction_tax=10, broker_fee=5
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Ensure this value is greater than or equal to 1.", str(response.content)
        )
        self.assertEqual(item.sold_quantity(), 0)

    def test_can_list_a_sub_quantity_of_an_item(self):
        # Given there is a basic fleet with a two items
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=10)
        market_order = self.list_item(
            item, quantity=1, listed_at_price=10000, transaction_tax=10, broker_fee=5
        )
        self.market_order_sold(market_order)
        self.assertEqual(self.user.isk_balance(), isk(8500))
        second_market_order = self.list_item(
            item, quantity=9, listed_at_price=1000, transaction_tax=10, broker_fee=5
        )
        self.market_order_sold(second_market_order)
        self.assertEqual(self.user.isk_balance(), isk(8500 + 850 * 9))

    def test_cant_list_a_zero_quantity_of_a_stack(self):
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=10)
        self.stack_items(item.location)
        item.refresh_from_db()
        response = self.list_stack_returning_reponse(
            item.stack,
            quantity=0,
            listed_at_price=10000,
            transaction_tax=10,
            broker_fee=5,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Ensure this value is greater than or equal to 1.", str(response.content)
        )
        self.assertEqual(item.sold_quantity(), 0)

    def test_cant_list_a_quantity_greater_than_item_quantity_of_a_stack(self):
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=10)
        self.stack_items(item.location)
        item.refresh_from_db()
        if item.stack is None:
            raise AssertionError("Missing Stack")
        response = self.list_stack_returning_reponse(
            item.stack,
            quantity=item.stack.quantity() + 1,
            listed_at_price=10000,
            transaction_tax=10,
            broker_fee=5,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Ensure this value is less than or equal to 10.", str(response.content)
        )
        self.assertEqual(item.sold_quantity(), 0)

    def test_cant_list_a_negative_quantity_of_a_stack(self):
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=10)
        self.stack_items(item.location)
        item.refresh_from_db()
        response = self.list_stack_returning_reponse(
            item.stack,
            quantity=-1,
            listed_at_price=10000,
            transaction_tax=10,
            broker_fee=5,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Ensure this value is greater than or equal to 1.", str(response.content)
        )
        self.assertEqual(item.sold_quantity(), 0)

    def test_can_list_a_sub_quantity_of_an_item_of_a_stack(self):
        # Given there is a basic fleet with an item
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=10)
        # And it is stacked
        self.stack_items(item.location)

        item.refresh_from_db()
        original_stack = item.stack
        # Sell 1 item in the stack
        self.list_item_stack(
            original_stack,
            quantity=1,
            listed_at_price=10000,
            transaction_tax=10,
            broker_fee=5,
        )
        # By selling a subquantity of the stack, a new stack is made just for the portion which sold.
        item.refresh_from_db()
        split_off_stack = StackedInventoryItem.objects.last()
        if split_off_stack is None:
            raise AssertionError("Missing Stack")
        self.stack_market_order_sold(split_off_stack)
        self.assertEqual(self.user.isk_balance(), isk(8500))

        # Sell the rest of the stack at a lower price
        self.list_item_stack(
            original_stack,
            quantity=9,
            listed_at_price=1000,
            transaction_tax=10,
            broker_fee=5,
        )
        self.stack_market_order_sold(original_stack)
        self.assertEqual(self.user.isk_balance(), isk(8500 + 850 * 9))

    def test_can_list_a_sub_quantity_of_stack_consuming_all_of_one_sub_item_and_a_bit_of_the_rest(
        self,
    ):
        # Given there is a basic fleet with a two items
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        item = self.an_item(loot_group, item_quantity=10)
        loot_group2 = self.a_loot_group(fleet)
        self.an_item(loot_group2, item_quantity=10)

        # And we stack them into a stack of 20
        self.stack_items(item.location)
        item.refresh_from_db()
        original_stack = item.stack
        # We sell 11 of the stack, which will sell 10 of the first item and 1 of the second
        self.list_item_stack(
            original_stack,
            quantity=11,
            listed_at_price=10000,
            transaction_tax=10,
            broker_fee=5,
        )

        # By selling a subquantity of the stack, a new stack is made just for the portion which sold.
        item.refresh_from_db()
        split_off_stack = StackedInventoryItem.objects.last()

        self.stack_market_order_sold(split_off_stack)
        self.assertEqual(self.user.isk_balance(), isk(8500 * 11))

        # Then we sell the rest of the stack.
        self.list_item_stack(
            original_stack,
            quantity=9,
            listed_at_price=1000,
            transaction_tax=10,
            broker_fee=5,
        )
        self.stack_market_order_sold(original_stack)
        self.assertEqual(self.user.isk_balance(), isk(8500 * 11 + 850 * 9))

    def test_complex_sub_splitting_example_with_multiple_buckets_and_price_chages(
        self,
    ):
        # Given there is a fleet with a three items
        fleet = self.a_fleet()
        loot_group = self.a_loot_group(fleet)
        loot_group2 = self.a_loot_group(fleet)

        self.a_loot_share(loot_group, self.char, share_quantity=1, flat_percent_cut=5)
        self.a_loot_share(loot_group, self.other_char, share_quantity=1)
        self.a_loot_share(loot_group2, self.other_char, share_quantity=1)

        item = self.an_item(loot_group, item_quantity=10)
        self.an_item(loot_group2, item_quantity=10)
        # And we stack some of the items
        self.stack_items(item.location)
        # And then another item of a different type is added
        self.an_item(loot_group2, item=self.another_item, item_quantity=10)

        item.refresh_from_db()
        original_stack = item.stack
        # We sell 11 of the stack, which will sell 10 of the first item and 1 of the second
        self.list_item_stack(
            original_stack,
            quantity=11,
            listed_at_price=10000,
            transaction_tax=10,
            broker_fee=5,
        )

        # By selling a subquantity of the stack, a new stack is made just for the portion which sold.
        item.refresh_from_db()
        split_off_stack = StackedInventoryItem.objects.last()

        self.stack_market_order_sold(split_off_stack)
        self.assertEqual(self.user.isk_balance(), isk(8500 * 11))

        # Then we sell the rest of the stack.
        self.list_item_stack(
            original_stack,
            quantity=9,
            listed_at_price=1000,
            transaction_tax=10,
            broker_fee=5,
        )
        self.stack_market_order_sold(original_stack)
        self.assertEqual(self.user.isk_balance(), isk(8500 * 11 + 850 * 9))
