from django.conf import settings
from django.db import models

from goosetools.items.models import Item
from goosetools.users.models import Character


class ShipOrder(models.Model):
    PAYMENT_METHODS = [("eggs", "eggs"), ("isk", "isk")]
    recipient_character = models.ForeignKey(Character, on_delete=models.CASCADE)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    ship = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField()
    state = models.TextField()
    notes = models.TextField(blank=True)
    payment_method = models.TextField(choices=PAYMENT_METHODS)
