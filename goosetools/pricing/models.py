from django.conf import settings
from django.core.exceptions import ValidationError
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
from goosetools.venmo.models import VirtualCurrency, create_access_controller

DATA_SET_TYPES = [("raw_market_data", "raw_market_data"), ("order", "order")]

DATA_SET_API_TYPES = [
    ("eve_echoes_market", "eve_echoes_market.com"),
    ("google_sheet", "A Google Sheet"),
    ("manual", "Manually Entered In " + settings.SITE_NAME),
]


class DataSet(models.Model):
    owner = models.ForeignKey(
        GooseUser, on_delete=models.CASCADE, null=True, blank=True
    )
    name = models.TextField(unique=True)
    description = models.TextField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)
    access_controller = models.ForeignKey(
        CrudAccessController,
        on_delete=models.CASCADE,
        default=create_access_controller,
    )
    api_type = models.TextField(choices=DATA_SET_API_TYPES)
    data_set_type = models.TextField(
        choices=DATA_SET_TYPES,
        default="raw_market_data",
    )
    google_sheet_id = models.TextField(null=True, blank=True)
    google_sheet_cell_range = models.TextField(null=True, blank=True)
    google_sheet_unique_key_column = models.TextField(null=True, blank=True)
    google_sheet_item_column = models.TextField(null=True, blank=True)

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
                other_default = DataSet.objects.get(default=True)
                if self != other_default:
                    other_default.default = False
                    other_default.save()
            except DataSet.DoesNotExist:
                pass
        if (
            not self.default
            and DataSet.objects.filter(default=True).exclude(pk=self.pk).count() == 0
        ):
            raise ValidationError(
                "Cannot un-set the default data set, instead mark the a new data "
                "set as default. "
            )
        super().save(*args, **kwargs)

    @staticmethod
    def get_default():
        return DataSet.objects.get(default=True)

    @staticmethod
    def ensure_default_exists():
        if DataSet.objects.count() == 0:
            DataSet.objects.create(
                name="eve_echoes_market",
                description="Market data sourced from https://eve-echoes-market.com/",
                tags="eve_echoes_market,raw_data,third_party",
                access_controller=CrudAccessController.objects.create(),
            )

    def __str__(self):
        return str(self.name) + (" (default)" if self.default else "")


class DataType(models.Model):
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE)
    name = models.TextField()
    google_sheet_column = models.TextField(null=True, blank=True)

    currency = models.ForeignKey(
        VirtualCurrency, on_delete=models.CASCADE, blank=True, null=True
    )

    class Meta:
        indexes = [models.Index(fields=["data_set"])]
        unique_together = [["data_set", "name"]]


class DataPoint(models.Model):
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE)
    data_type = models.ForeignKey(DataType, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, blank=True, null=True)
    time = models.DateTimeField(auto_now=True)
    unique_key = models.TextField(blank=True, null=True)
    decimal_value = models.DecimalField(
        max_digits=22, decimal_places=4, blank=True, null=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["data_set", "data_type", "time", "item", "unique_key"])
        ]
        unique_together = [["data_set", "unique_key"]]


class LatestDataPoint(models.Model):
    data_set = models.ForeignKey(DataSet, on_delete=models.CASCADE)
    data_type = models.ForeignKey(DataType, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, blank=True, null=True)
    point = models.ForeignKey(DataPoint, on_delete=models.CASCADE)

    class Meta:
        indexes = [models.Index(fields=["data_set", "data_type"])]
        unique_together = ["data_set", "data_type"]

    def __str__(self):
        return f"Latest {str(self.point)}"


class ItemMarketDataEvent(models.Model):
    price_list = models.ForeignKey(DataSet, on_delete=models.CASCADE)
    unique_user_id = models.TextField(
        blank=True,
        null=True,
        unique=True,
        help_text="An optional unique ID you want to give this price.",
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    manual_override_price = models.BooleanField(
        default=False,
        help_text="If this price should override any current or future automatically "
        "downloaded prices.",
    )
    time = models.DateTimeField(help_text="The time this price is for.")
    sell = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    buy = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    lowest_sell = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    highest_buy = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    volume = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    def get_absolute_url(self):
        return reverse("pricing:event-detail", kwargs={"pk": self.pk})

    class Meta:
        indexes = [models.Index(fields=["price_list", "-time", "item"])]
        unique_together = [
            ["price_list", "unique_user_id", "item", "time"],
        ]

    def __str__(self):
        return f"Market Price for {self.item}@{self.time}: ls={self.lowest_sell}, hb={self.highest_buy}, s={self.sell}, b={self.buy}"


class LatestItemMarketDataEvent(models.Model):
    price_list = models.ForeignKey(
        DataSet, on_delete=models.CASCADE, null=True, blank=True
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    time = models.DateTimeField()
    event = models.ForeignKey(ItemMarketDataEvent, on_delete=models.CASCADE)

    class Meta:
        indexes = [models.Index(fields=["price_list", "item", "time"])]
        unique_together = ["price_list", "item"]

    def __str__(self):
        return f"Latest {str(self.event)}"
