import json
import math as m
from decimal import Decimal

from django.db import models
from django.utils import timezone, translation
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from moneyed.localization import format_money

from goosetools.core.models import System
from goosetools.notifications.notification_types import NOTIFICATION_TYPES
from goosetools.ownership.models import TransferLog
from goosetools.users.models import Character, GooseUser


class JSONEncoderWithMoneyAndDecimalSupport(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Money):
            return format_money(o, locale=translation.get_language())
        if isinstance(o, Decimal):
            return str(m.floor(o))
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, o)


class Contract(models.Model):
    from_user = models.ForeignKey(
        GooseUser, on_delete=models.CASCADE, related_name="my_contracts"
    )
    to_char = models.ForeignKey(Character, on_delete=models.CASCADE)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    transfer = models.ForeignKey(
        TransferLog, on_delete=models.CASCADE, null=True, blank=True
    )
    created = models.DateTimeField()
    status = models.TextField(
        choices=[
            (
                "requested",
                "requested",
            ),
            # A requested contract is the system asking from_user to make a contract to to_char
            ("pending", "pending"),
            ("rejected", "rejected"),
            ("accepted", "accepted"),
            ("cancelled", "cancelled"),
        ]
    )
    log = models.JSONField(null=True, blank=True)  # type: ignore
    logged_quantity = models.IntegerField(default=0)
    isk = MoneyField(
        max_digits=20, decimal_places=2, default_currency="EEI", default=0
    )  # If positive then from_user is sending to_char isk, Negative then from_user will be recieving isk from to_char

    def change_status(self, new_status):
        if new_status != "pending":
            if self.status == "requested":
                NOTIFICATION_TYPES["contract_requested"].dismiss_one(self.from_user)
            else:
                NOTIFICATION_TYPES["contract_made"].dismiss_one(self.to_char.user)
        self.status = new_status

    def isk_display(self):

        # pylint: disable=no-member
        isk_amount = self.isk.amount
        if isk_amount == 0:
            return "0"
        elif isk_amount > 0:
            return (
                f"{self.from_user} pays {self.to_char}({self.to_char.user}) {self.isk}"
            )
        else:
            return (
                f"{self.to_char}({self.to_char.user}) pays {self.from_user} {-self.isk}"
            )

    @staticmethod
    def create(from_user, to_char, system, status, isk=0, transfer=None):
        contract = Contract(
            from_user=from_user,
            to_char=to_char,
            system=system,
            created=timezone.now(),
            status=status,
            isk=isk,
            transfer=transfer,
        )
        if status == "requested":
            NOTIFICATION_TYPES["contract_requested"].send(from_user)
        else:
            NOTIFICATION_TYPES["contract_made"].send(to_char.user)
        contract.full_clean()
        contract.save()
        return contract

    def save_items_to_log(self, clear_items=True):
        log = []
        for item in self.inventoryitem_set.all():
            log.append(
                {
                    "id": item.id,
                    "item": str(item),
                    "quantity": item.quantity,
                    "status": item.status(),
                    "loot_group_id": item.loot_group and item.loot_group.id,
                }
            )
        self.log = json.dumps(log, cls=JSONEncoderWithMoneyAndDecimalSupport)
        self.logged_quantity = self.inventoryitem_set.count()
        self.full_clean()
        self.save()
        if clear_items:
            self.inventoryitem_set.update(contract=None)

    def can_change_status_to(self, user, new_status):
        is_recieving_user = self.to_char.user == user
        is_sending_user = self.from_user == user
        if self.status == "requested":
            if new_status == "cancelled":
                return is_recieving_user
            elif new_status in ("rejected", "pending"):
                return is_sending_user
            else:
                return False
        elif self.status == "pending":
            return (
                is_recieving_user
                and new_status in ["accepted", "rejected"]
                or is_sending_user
                and new_status in ["cancelled"]
            )
        else:
            return False

    def total_items(self):
        return self.inventoryitem_set.count() + self.logged_quantity
