from django.db import models
from django.db.models import Min
from django.db.models.aggregates import Sum
from django.forms import forms
from django.utils import timezone
from djmoney.money import Money

from goosetools.contracts.models import Contract
from goosetools.core.models import System
from goosetools.ownership.models import LootGroup
from goosetools.users.models import Character, Corp


def to_isk(num):
    return Money(amount=round(num, 2), currency="EEI")


def model_sum(queryset, key):
    result = queryset.aggregate(result=Sum(key))["result"]
    if result is None:
        return 0
    else:
        return result


class ItemType(models.Model):
    name = models.TextField()

    def __str__(self):
        return str(self.name)


class ItemSubType(models.Model):
    item_type = models.ForeignKey(ItemType, on_delete=models.CASCADE)
    name = models.TextField()

    def __str__(self):
        return str(self.name)


class ItemSubSubType(models.Model):
    item_sub_type = models.ForeignKey(ItemSubType, on_delete=models.CASCADE)
    name = models.TextField()

    def __str__(self):
        return str(self.name)


class Item(models.Model):
    item_type = models.ForeignKey(ItemSubSubType, on_delete=models.CASCADE)
    name = models.TextField(primary_key=True)
    eve_echoes_market_id = models.TextField(null=True, blank=True, unique=True)
    cached_lowest_sell = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )

    def latest_market_data(self):
        return self.itemmarketdataevent_set.order_by("-time").first()

    def min_of_last_x_hours(self, hours):
        time_threshold = timezone.now() - timezone.timedelta(hours=hours)
        min_price = self.itemmarketdataevent_set.filter(
            time__gte=time_threshold
        ).aggregate(min_lowest_sell=Min("lowest_sell"))["min_lowest_sell"]
        min_price_other = self.itemmarketdataevent_set.filter(
            time__gte=time_threshold
        ).aggregate(min_sell=Min("sell"))["min_sell"]
        datapoints_used = (
            self.itemmarketdataevent_set.filter(time__gte=time_threshold)
            .values("lowest_sell")
            .distinct()
            .count()
        )
        return min_price, datapoints_used, min_price_other

    def lowest_sell(self):
        if not self.cached_lowest_sell:
            result = self.latest_market_data() and self.latest_market_data().lowest_sell
            self.cached_lowest_sell = result
        return self.cached_lowest_sell

    @staticmethod
    def all_ships():
        return Item.objects.filter(
            item_type__item_sub_type__item_type__name="Ships"
        ).all()

    class Meta:
        indexes = [models.Index(fields=["-cached_lowest_sell"])]

    def __str__(self):
        return f"{str(self.name)}"


class Station(models.Model):
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    name = models.TextField(primary_key=True)


class CorpHanger(models.Model):
    corp = models.ForeignKey(Corp, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    hanger = models.CharField(
        max_length=1,
        choices=[
            ("1", "Hanger 1"),
            ("2", "Hanger 2"),
            ("3", "Hanger 3"),
            ("4", "Hanger 4"),
        ],
    )

    def __str__(self):
        return f"In [{self.corp.name}] Corp {self.hanger} at {self.station} "


class CharacterLocation(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    system = models.ForeignKey(System, on_delete=models.CASCADE, null=True, blank=True)

    def has_admin(self, user):
        for char in user.characters():
            if self.character == char:
                return True
        return False

    def __str__(self):
        if not self.system:
            return f"Space On {self.character.ingame_name}({self.character.display_name()})"
        else:
            return f"{self.system.name} On {self.character.ingame_name}({self.character.display_name()})"


class ItemLocation(models.Model):
    character_location = models.ForeignKey(
        CharacterLocation, on_delete=models.CASCADE, blank=True, null=True
    )
    corp_hanger = models.ForeignKey(
        CorpHanger, on_delete=models.CASCADE, blank=True, null=True
    )

    def has_admin(self, user):
        # TODO support corp hanger permisions
        for char in user.characters():
            if self.character_location and self.character_location.character == char:
                return True
        return False

    def clean(self):
        if self.character_location and self.corp_hanger:
            raise forms.ValidationError(
                "An item cannot be located both on a character and in a corp hanger."
            )
        if not self.character_location and not self.corp_hanger:
            raise forms.ValidationError(
                "An item must be either on a character or in a corp hanger."
            )

    def in_station(self):
        return (not self.character_location) or self.character_location.system

    def __str__(self):
        if self.character_location:
            return str(self.character_location)
        else:
            return str(self.corp_hanger)


class StackedInventoryItem(models.Model):
    created_at = models.DateTimeField()

    def _first_item(self):
        items = self.inventoryitem_set.count()
        if items > 0:
            return self.inventoryitem_set.first()
        else:
            return False

    def junk(self):
        for item in self.inventoryitem_set.all():
            item.junk()

    def unjunk(self):
        for item in self.inventoryitem_set.all():
            item.junkeditem.unjunk()

    def item(self):
        return self._first_item() and self._first_item().item

    def marketorder(self):
        # pylint: disable=no-member
        items = self.marketorders()  # type: ignore
        if items.count() > 0:
            return items.first()
        else:
            return False

    def estimated_profit(self):
        lowest_sell = self._first_item() and self._first_item().item.lowest_sell()
        return lowest_sell and to_isk(
            (self.order_quantity() + self.quantity()) * lowest_sell
        )

    # TODO Reverse Dep
    def order_quantity(self):
        return model_sum(self.inventoryitem_set, "marketorder__quantity")

    def quantity(self):
        return model_sum(InventoryItem.objects.filter(stack=self.id), "quantity")

    # TODO Reverse Dep
    def sold_quantity(self):
        return model_sum(self.inventoryitem_set, "solditem__quantity")

    def total_quantity(self):
        return self.order_quantity() + self.quantity() + self.sold_quantity()

    def total_quantity_display(self):
        quantity = self.quantity()
        orders = self.order_quantity()
        sold = self.sold_quantity()
        status = ""
        if quantity > 0:
            status = status + f"{quantity} Waiting "
        if orders > 0:
            status = status + f"{orders} Selling "
        if sold > 0:
            status = status + f"{sold} Sold "
        return status

    def can_edit(self):
        return self._first_item() and self._first_item().can_edit()

    def buy_sell(self):
        return self.marketorder() and self.marketorder().buy_or_sell

    def internal_external(self):
        return self.marketorder() and self.marketorder().internal_or_external

    def list_price(self):
        return self.marketorder() and self.marketorder().listed_at_price

    def loc(self):
        items = self.inventoryitem_set.count()
        if items > 0:
            return self.inventoryitem_set.first().location  # type: ignore
        else:
            return False

    def items(self):
        return self.inventoryitem_set.all()

    def has_admin(self, user):
        items = self.inventoryitem_set.count()
        if items > 0:
            return self.inventoryitem_set.first().has_admin(user)  # type: ignore
        else:
            return True

    def can_sell(self):
        return self._first_item() and self._first_item().can_sell()

    def item_info(self):
        return self._first_item() and self._first_item().item

    def __str__(self):
        return f"Stack of {self.item_info()} x ({self.total_quantity_display()})"


class InventoryItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField()
    location = models.ForeignKey(ItemLocation, on_delete=models.CASCADE)
    loot_group = models.ForeignKey(
        LootGroup, on_delete=models.SET_NULL, null=True, blank=True
    )
    contract = models.ForeignKey(
        Contract, on_delete=models.SET_NULL, null=True, blank=True
    )
    stack = models.ForeignKey(
        StackedInventoryItem, on_delete=models.SET_NULL, null=True, blank=True
    )

    def has_admin(self, user):
        return self.location.has_admin(user)

    def isk_balance(self):
        return to_isk(model_sum(self.isktransaction_set, "isk"))  # type: ignore

    def egg_balance(self):
        return to_isk(model_sum(self.eggtransaction_set, "eggs"))  # type: ignore

    def isk_and_eggs_balance(self):
        return self.isk_balance() + self.egg_balance()

    def order_quantity(self):
        # pylint: disable=no-member
        if hasattr(self, "marketorder"):
            return self.marketorder.quantity
        else:
            return 0

    def sold_quantity(self):
        # pylint: disable=no-member
        if hasattr(self, "solditem"):
            return self.solditem.quantity
        else:
            return 0

    def junked_quantity(self):
        # pylint: disable=no-member
        if hasattr(self, "junkeditem"):
            return self.junkeditem.quantity
        else:
            return 0

    def total_quantity(self):
        return sum(
            [
                self.quantity,
                self.order_quantity(),
                self.sold_quantity(),
                self.junked_quantity(),
            ]
        )

    def can_sell(self):
        return self.quantity > 0 and not self.contract

    def can_edit(self):
        return (
            not hasattr(self, "marketorder")
            and not hasattr(self, "solditem")
            and not hasattr(self, "junkeditem")
            and not self.contract
        )

    def add(self, quantity):
        if self.can_edit():
            resulting_quantity = self.quantity + quantity
            if resulting_quantity == 0:
                self.delete()
                return True
            elif resulting_quantity < 0:
                return False
            self.quantity = resulting_quantity
            self.full_clean()
            self.save()
            return True
        else:
            return False

    def junk(self):
        junk_item = JunkedItem(item=self, quantity=self.quantity, reason="Manual")
        junk_item.full_clean()
        junk_item.save()
        self.quantity = 0
        self.full_clean()
        self.save()

    def estimated_profit(self):
        lowest_sell = self.item.lowest_sell()
        return lowest_sell and to_isk(
            (self.quantity + self.order_quantity() + self.junked_quantity())
            * lowest_sell
        )

    def status(self):
        status = ""
        if self.quantity != 0:
            if self.contract:
                status = status + " In Pending Contract"
            else:
                status = status + f" {self.quantity} Waiting"
        if self.stack:
            status = status + " Stacked"
        quantity_listed = self.order_quantity()
        if quantity_listed != 0:
            status = status + f" {quantity_listed} Listed"
        quantity_sold = self.sold_quantity()
        if quantity_sold != 0:
            # pylint: disable=no-member
            status = status + f" {quantity_sold} Sold ({self.solditem.status()})"
        quantity_junked = self.junked_quantity()
        if quantity_junked != 0:
            status = status + f" {quantity_junked} Junked"

        isk = self.isk_balance()
        if isk.amount != 0:
            status = status + f", Profit:{isk}"
        egg = self.egg_balance()
        if egg.amount != 0:
            status = status + f", Eggs Profit:{egg}"

        return status

    def __str__(self):
        return f"{self.item} x {self.total_quantity()} @ {self.location}"

    class Meta:
        indexes = [models.Index(fields=["stack", "location", "loot_group", "contract"])]


class JunkedItem(models.Model):
    item = models.OneToOneField(InventoryItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    reason = models.TextField()

    def unjunk(self):
        item = self.item
        item.quantity = self.quantity
        item.full_clean()
        item.save()
        self.delete()
