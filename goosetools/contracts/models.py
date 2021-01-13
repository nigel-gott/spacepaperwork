from django.conf import settings
from django.db import models

from goosetools.core.models import System
from goosetools.users.models import Character


class Contract(models.Model):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="my_contracts"
    )
    to_char = models.ForeignKey(Character, on_delete=models.CASCADE)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    created = models.DateTimeField()
    status = models.TextField(
        choices=[
            ("pending", "pending"),
            ("rejected", "rejected"),
            ("accepted", "accepted"),
            ("cancelled", "cancelled"),
        ]
    )
    log = models.JSONField(null=True, blank=True)  # type: ignore

    def can_accept_or_reject(self, user):
        return self.status == "pending" and self.to_char.user == user

    def can_cancel(self, user):
        return self.status == "pending" and self.from_user == user

    def total_items(self):
        return self.inventoryitem_set.count()
