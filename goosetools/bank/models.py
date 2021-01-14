from django.db import models
from django.db.models.aggregates import Sum
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from goosetools.items.models import InventoryItem
from goosetools.users.models import GooseUser


def to_isk(num):
    return Money(amount=round(num, 2), currency="EEI")


def model_sum(queryset, key):
    result = queryset.aggregate(result=Sum(key))["result"]
    if result is None:
        return 0
    else:
        return result


class IskTransaction(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    time = models.DateTimeField()
    isk = MoneyField(max_digits=20, decimal_places=2, default_currency="EEI")
    transaction_type = models.TextField(
        choices=[
            ("price_change_broker_fee", "Price Change Broker Fee"),
            ("broker_fee", "Broker Fee"),
            ("transaction_tax", "Transaction Tax"),
            ("contract_broker_fee", "Contract Broker Fee"),
            ("contract_transaction_tax", "Contract Transaction Tax"),
            ("contract_gross_profit", "Contract Gross Profit"),
            (
                "external_market_price_adjustment_fee",
                "InGame Market Price Adjustment Fee",
            ),
            ("external_market_gross_profit", "InGame Market Gross Profit"),
            ("egg_deposit", "Egg Deposit"),
            ("fractional_remains", "Fractional Remains"),
            ("buyback", "Buy Back"),
        ]
    )
    notes = models.TextField(default="", blank=True)

    def __str__(self):
        return f"Isk Transaction @ {self.time} for {self.isk} of type {self.transaction_type} with notes: '{self.notes}'"

    @staticmethod
    def user_isk_transactions(user: GooseUser):
        return IskTransaction.objects.filter(
            item__location__character_location__character__user=user
        )

    class Meta:
        indexes = [models.Index(fields=["time"])]


class EggTransaction(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    time = models.DateTimeField()
    eggs = MoneyField(max_digits=20, decimal_places=2, default_currency="EEI")
    debt = models.BooleanField(default=True)
    counterparty = models.ForeignKey(GooseUser, on_delete=models.CASCADE)
    notes = models.TextField(default="", blank=True)

    def __str__(self):
        return f"{self.counterparty} - {self.item.id} - {self.quantity} - {self.time} - {self.eggs} - Debt:{self.debt} - {self.notes}"

    @staticmethod
    def user_egg_transactions(user: GooseUser):
        return EggTransaction.objects.filter(counterparty=user)

    class Meta:
        indexes = [models.Index(fields=["time"])]


def isk_balance(self):
    return to_isk(
        model_sum(
            IskTransaction.objects.filter(
                item__location__character_location__character__user=self
            ),
            "isk",
        )
    )


def debt_egg_balance(self):
    return to_isk(
        model_sum(
            EggTransaction.objects.filter(counterparty=self, debt=True),
            "eggs",
        )
    )


def egg_balance(self):
    return to_isk(
        model_sum(
            EggTransaction.objects.filter(counterparty=self, debt=False),
            "eggs",
        )
    )


# TODO Fix dependency ordering instead of monkey patching
GooseUser.isk_balance = isk_balance  # type: ignore
GooseUser.egg_balance = egg_balance  # type: ignore
GooseUser.debt_egg_balance = debt_egg_balance  # type: ignore
