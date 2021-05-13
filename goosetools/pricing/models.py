from django.db import models

from goosetools.items.models import Item
from goosetools.users.models import CrudAccessController, GooseUser


class ItemMarketDataEvent(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    time = models.DateTimeField()
    sell = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    buy = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    lowest_sell = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    highest_buy = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    volume = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["-time"])]
        unique_together = (("item", "time"),)

    def __str__(self):
        return f"Market Price for {self.item}@{self.time}: ls={self.lowest_sell}, hb={self.highest_buy}, s={self.sell}, b={self.buy}"


class PriceList(models.Model):
    owner = models.ForeignKey(GooseUser, on_delete=models.CASCADE)
    name = models.TextField()
    description = models.TextField()
    tags = models.TextField()
    access_controller = models.ForeignKey(
        CrudAccessController, on_delete=models.SET_NULL, null=True, blank=True
    )
