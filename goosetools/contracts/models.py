from django.db import models
from django.utils import timezone
from djmoney.models.fields import MoneyField

from goosetools.core.models import System
from goosetools.notifications.notification_types import NOTIFICATION_TYPES
from goosetools.users.models import Character, GooseUser


class Contract(models.Model):
    from_user = models.ForeignKey(
        GooseUser, on_delete=models.CASCADE, related_name="my_contracts"
    )
    to_char = models.ForeignKey(Character, on_delete=models.CASCADE)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    created = models.DateTimeField()
    status = models.TextField(
        choices=[
            (
                "requested",
                "requested",
            ),  # A requested contract is the system asking from_user to make a contract to to_char
            ("pending", "pending"),
            ("rejected", "rejected"),
            ("accepted", "accepted"),
            ("cancelled", "cancelled"),
        ]
    )
    log = models.JSONField(null=True, blank=True)  # type: ignore
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
                f"{self.to_char}({self.to_char.user}) pays {self.from_user} {self.isk}"
            )

    @staticmethod
    def create(from_user, to_char, system, status, isk=0):
        contract = Contract(
            from_user=from_user,
            to_char=to_char,
            system=system,
            created=timezone.now(),
            status=status,
            isk=isk,
        )
        if status == "requested":
            NOTIFICATION_TYPES["contract_requested"].send(from_user)
        else:
            NOTIFICATION_TYPES["contract_made"].send(to_char.user)
        contract.full_clean()
        contract.save()
        return contract

    def can_accept_or_reject(self, user):
        return self.status == "pending" and self.to_char.user == user

    def can_cancel(self, user):
        return self.status == "pending" and self.from_user == user

    def total_items(self):
        return self.inventoryitem_set.count()
