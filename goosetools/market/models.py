import math as m

from django.db import models, transaction
from django.db.models.aggregates import Sum
from django.db.models.expressions import F
from django.utils import timezone
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from goosetools.bank.models import IskTransaction
from goosetools.items.models import InventoryItem, StackedInventoryItem
from goosetools.ownership.models import TransferLog
from goosetools.users.models import GooseUser


def to_isk(num):
    return Money(amount=round(num, 2), currency="EEI")


def model_sum(queryset, key):
    result = queryset.aggregate(result=Sum(key))["result"]
    if result is None:
        return 0
    else:
        return result


class MarketOrder(models.Model):
    item = models.OneToOneField(InventoryItem, on_delete=models.CASCADE)
    internal_or_external = models.TextField(
        choices=[("internal", "Internal"), ("external", "External")]
    )
    buy_or_sell = models.TextField(choices=[("buy", "Buy"), ("sell", "Sell")])
    quantity = models.PositiveIntegerField()
    listed_at_price = MoneyField(
        max_digits=20, decimal_places=2, default_currency="EEI"
    )
    transaction_tax = models.DecimalField(max_digits=5, decimal_places=2)
    broker_fee = models.DecimalField(max_digits=5, decimal_places=2)

    def has_admin(self, user):
        return self.item.has_admin(user)

    # TODO Moved here to fix circular dep, find better location.
    def add_isk_transaction(self, isk, transaction_type, quantity, notes, user):
        item = self.item
        if not item.has_admin(user):
            return (
                False,
                f"{user} doesn't have permissions to add an isk transaction for {item}",
            )
        else:
            new_isk_transaction = IskTransaction(
                isk=isk,
                transaction_type=transaction_type,
                quantity=quantity,
                notes=notes,
                time=timezone.now(),
                item=item,
            )
            new_isk_transaction.full_clean()
            new_isk_transaction.save()
            return True, f"Successfully added: {new_isk_transaction}"

    def change_price(self, new_price, broker_fee, changing_user):
        if not self.has_admin(changing_user):
            return (
                False,
                f"You do not have permissions as {changing_user} to edit the price of {self}",
            )

        with transaction.atomic():
            old_price = self.listed_at_price.amount
            if new_price == old_price:
                return False, "The new price must be different from the old price."
            else:
                if old_price > new_price:
                    notes = f"Market Price Was Reduced from {old_price} to {new_price}"
                    fee = to_isk(m.floor(new_price * self.quantity * broker_fee / 2))
                else:
                    notes = (
                        f"Market Price Was Increased from {old_price} to {new_price}"
                    )
                    fee = to_isk(
                        m.floor(
                            (new_price - old_price / 2) * self.quantity * broker_fee
                        )
                    )
                self.listed_at_price = to_isk(new_price)
                self.full_clean()
                self.save()
                return self.add_isk_transaction(
                    -fee,
                    "price_change_broker_fee",
                    self.quantity,
                    notes,
                    changing_user,
                )

    def __str__(self):
        return f"A {self.buy_or_sell} of {self.item.item} x {self.quantity} listed for {self.listed_at_price} @ {self.internal_or_external} market"


class SoldItem(models.Model):
    item = models.OneToOneField(InventoryItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    sold_via = models.TextField(
        choices=[
            ("internal", "Internal Market"),
            ("external", "External Market"),
            ("contract", "Contract"),
        ]
    )
    transfered = models.BooleanField(default=False)
    transfered_quantity = models.PositiveIntegerField(default=0)
    transfer_log = models.ForeignKey(
        TransferLog, on_delete=models.SET_NULL, null=True, blank=True
    )

    def transfered_so_far(self):
        return self.quantity_to_transfer() == 0

    def quantity_to_transfer(self):
        return self.quantity - self.transfered_quantity

    def isk_balance(self):
        return self.item.isk_balance()

    def isk_and_eggs_balance(self):
        return self.item.isk_and_eggs_balance()

    def status(self):
        if self.quantity_to_transfer() == 0:
            return "All Sold Transfered!"
        elif self.transfered_quantity > 0:
            return f"{self.quantity_to_transfer()} Pending, {self.transfered_quantity} Transfered Already!"
        else:
            return f"{self.quantity_to_transfer()} Pending Transfer"

    def __str__(self):
        return f"{self.item} x {self.quantity} Sold x {self.transfered_quantity} Transfered - via: {self.sold_via}"


def can_deposit(self):
    return (
        SoldItem.objects.filter(
            item__location__character_location__character__discord_user=self.discord_user,
            quantity__gt=F("transfered_quantity"),
        ).count()
        > 0
    )


# TODO Fix dependency ordering instead of monkey patching
GooseUser.can_deposit = can_deposit  # type: ignore


def marketorders(self):
    return MarketOrder.objects.filter(item__stack=self.id).order_by("item__created_at")


StackedInventoryItem.marketorders = marketorders  # type: ignore
