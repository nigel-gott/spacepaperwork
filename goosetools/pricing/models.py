from django.db import models

from goosetools.items.models import Item
from goosetools.users.models import CrudAccessController, GooseUser


class PriceList(models.Model):
    owner = models.ForeignKey(
        GooseUser, on_delete=models.CASCADE, null=True, blank=True
    )
    name = models.TextField(unique=True)
    description = models.TextField()
    tags = models.TextField()
    access_controller = models.ForeignKey(
        CrudAccessController, on_delete=models.SET_NULL, null=True, blank=True
    )
    api_type = models.TextField(
        choices=[
            ("eve_echoes_market", "eve_echoes_market"),
            ("google_sheet", "google_sheet"),
            ("manual", "manual"),
        ]
    )
    google_sheet_id = models.TextField(null=True, blank=True)
    google_sheet_cell_range = models.TextField(null=True, blank=True)

    supports_orders = models.BooleanField(default=True)
    default = models.BooleanField(default=True)

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        if self.default:
            try:
                other_default = PriceList.objects.get(default=True)
                if self != other_default:
                    other_default.default = False
                    other_default.save()
            except PriceList.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    @staticmethod
    def get_active():
        return PriceList.objects.get(active=True)

    @staticmethod
    def ensure_default_exists():
        if PriceList.objects.count() == 0:
            PriceList.objects.create(
                name="eve_echoes_market",
                description="Market data sourced from https://eve-echoes-market.com/",
                tags="eve_echoes_market,raw_data,third_party",
                access_controller=CrudAccessController.objects.create(),
            )


class ItemMarketDataEvent(models.Model):
    price_list = models.ForeignKey(
        PriceList, on_delete=models.CASCADE, null=True, blank=True
    )
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
        indexes = [models.Index(fields=["price_list", "-time"])]
        unique_together = (("item", "time"),)

    def __str__(self):
        return f"Market Price for {self.item}@{self.time}: ls={self.lowest_sell}, hb={self.highest_buy}, s={self.sell}, b={self.buy}"
