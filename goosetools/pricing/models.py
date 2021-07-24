from django.conf import settings
from django.db import models
from django.urls import reverse

from goosetools.items.models import Item
from goosetools.users.models import (
    BASIC_ACCESS,
    SHIP_PRICE_ADMIN,
    CrudAccessController,
    GooseUser,
    PermissibleEntity,
)
from goosetools.venmo.models import create_access_controller

PRICE_LIST_PRICE_TYPES = [("raw_market_data", "raw_market_data"), ("order", "order")]

PRICE_LIST_API_TYPES = [
    ("eve_echoes_market", "eve_echoes_market.com"),
    ("google_sheet", "A Google Sheet"),
    ("manual", "Manually Entered In " + settings.SITE_NAME),
]


class PriceList(models.Model):
    owner = models.ForeignKey(
        GooseUser, on_delete=models.CASCADE, null=True, blank=True
    )
    name = models.TextField(unique=True)
    description = models.TextField()
    tags = models.TextField()
    access_controller = models.ForeignKey(
        CrudAccessController,
        on_delete=models.CASCADE,
        default=create_access_controller,
    )
    api_type = models.TextField(choices=PRICE_LIST_API_TYPES)
    price_type = models.TextField(
        choices=PRICE_LIST_PRICE_TYPES,
        default="raw_market_data",
        help_text="Controls how these prices are treated. If raw_market_data then each "
        "price is just treated as an immutable 'the price for this item at "
        "this time is this' piece of data. If order then instead treated as "
        "the fact that you want to buy or sell the volume of the item and if hooked "
        "up to a shop then will make said order available in the system. The order's "
        "volume with be automatically decreased as orders are completed in "
        "the system, unless a new row is imported with a new unique_user_id "
        "which will update the volume and hence the order quantity to that "
        "rows volume.",
    )
    google_sheet_id = models.TextField(null=True, blank=True)
    google_sheet_cell_range = models.TextField(null=True, blank=True)

    default = models.BooleanField(default=False)
    deletable = models.BooleanField(default=True)

    def get_absolute_url(self):
        return reverse("pricing:pricelist-detail", kwargs={"pk": self.pk})

    def built_in_permissible_entities(self, owner):
        admins = [
            PermissibleEntity.allow_perm(SHIP_PRICE_ADMIN, built_in=True),
        ]
        if owner is not None:
            admins.append(PermissibleEntity.allow_user(owner, built_in=True))
        return CrudAccessController.wrapper(
            adminable_by=admins,
        )

    def default_permissible_entities(self):
        return [
            ("view", PermissibleEntity.allow_perm(BASIC_ACCESS)),
            ("use", PermissibleEntity.allow_perm(BASIC_ACCESS)),
        ]

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

    def __str__(self):
        return str(self.name) + (" (default)" if self.default else "")


class ItemMarketDataEvent(models.Model):
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE)
    unique_user_id = models.TextField(blank=True, null=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    manual_override_price = models.BooleanField(default=False)
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
        indexes = [models.Index(fields=["price_list", "-time", "item"])]
        unique_together = ["price_list", "unique_user_id", "item", "time"]

    def __str__(self):
        return f"Market Price for {self.item}@{self.time}: ls={self.lowest_sell}, hb={self.highest_buy}, s={self.sell}, b={self.buy}"


class LatestItemMarketDataEvent(models.Model):
    price_list = models.ForeignKey(
        PriceList, on_delete=models.CASCADE, null=True, blank=True
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    time = models.DateTimeField()
    event = models.ForeignKey(ItemMarketDataEvent, on_delete=models.CASCADE)

    class Meta:
        indexes = [models.Index(fields=["price_list", "item", "time"])]
        unique_together = ["price_list", "item"]

    def __str__(self):
        return f"Latest {str(self.event)}"
