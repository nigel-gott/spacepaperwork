from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.db.models.aggregates import Max
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from goosetools.users.models import Character, GooseUser


def to_isk(num):
    return Money(amount=round(num, 2), currency="EEI")


class OrderLimitGroup(models.Model):
    name = models.TextField()
    days_between_orders = models.PositiveIntegerField()

    def ships(self):
        return [ship.name for ship in self.ship_set.all()]  # type:ignore

    def __str__(self):
        return f"{self.name} - days_between_orders:{self.days_between_orders}"


class Ship(models.Model):
    name = models.TextField(unique=True)
    tech_level = models.PositiveIntegerField()
    free = models.BooleanField(default=False)
    order_limit_group = models.ForeignKey(
        OrderLimitGroup, on_delete=models.SET_NULL, null=True, blank=True
    )
    isk_price = MoneyField(
        max_digits=20, decimal_places=2, default_currency="EEI", null=True, blank=True
    )
    eggs_price = MoneyField(
        max_digits=20, decimal_places=2, default_currency="EEI", null=True, blank=True
    )
    prices_last_updated = models.DateTimeField(null=True, blank=True)

    def valid_price(self):
        now_minus_1_hour = timezone.now() - timezone.timedelta(hours=1)
        return (
            self.isk_price is not None
            and self.eggs_price is not None
            and self.prices_last_updated is not None
            and self.prices_last_updated >= now_minus_1_hour
        )

    def clean(self):
        if not self.free and self.order_limit_group is not None:
            raise ValidationError(
                _(
                    "A Ship cannot be free and in a Order Limit Group. Either remove the group or make the ship free."
                )
            )

    def total_order_quantity(self):
        result = self.shiporder_set.aggregate(total=Sum("quantity"))  # type: ignore
        if result:
            return result["total"]
        else:
            return 0

    def total_order_quantity_last_month(self):
        now = timezone.now()
        now_minus_1_month = now - timezone.timedelta(weeks=4)
        result = self.shiporder_set.filter(created_at__gt=now_minus_1_month).aggregate(  # type: ignore
            total=Sum("quantity")
        )
        if result:
            return result["total"]
        else:
            return 0

    def last_order(self):
        result = self.shiporder_set.aggregate(max=Max("created_at"))  # type: ignore
        if result:
            return result["max"]
        else:
            return "Never Ordered"

    def total_isk_and_eggs_quantity(self):
        result = self.shiporder_set.aggregate(total=Sum("price"))  # type: ignore
        if result:
            return result["total"]
        else:
            return 0

    def total_isk_and_eggs_quantity_last_month(self):
        now = timezone.now()
        now_minus_1_month = now - timezone.timedelta(weeks=4)
        result = self.shiporder_set.filter(created_at__gt=now_minus_1_month).aggregate(  # type: ignore
            total=Sum("price")
        )
        if result:
            return result["total"]
        else:
            return 0

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        display = f"{self.name} (T{self.tech_level}) "
        if self.free:
            display = display + " - FREE"
        return display


class ShipOrder(models.Model):
    PAYMENT_METHODS = [
        ("eggs", "eggs"),
        ("isk", "isk"),
        ("free", "free"),
        ("srp", "srp"),
    ]
    recipient_character = models.ForeignKey(Character, on_delete=models.CASCADE)
    assignee = models.ForeignKey(
        GooseUser, on_delete=models.CASCADE, null=True, blank=True
    )
    contract_made = models.BooleanField(default=False)
    ship = models.ForeignKey(Ship, on_delete=models.CASCADE)
    uid = models.TextField(unique=True)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField()
    blocked_until = models.DateTimeField(null=True, blank=True)
    state = FSMField(default="not_started")
    notes = models.TextField(blank=True)
    payment_method = models.TextField(choices=PAYMENT_METHODS)
    price = MoneyField(
        max_digits=20, decimal_places=2, default_currency="EEI", null=True, blank=True
    )
    payment_taken = models.BooleanField(default=False)

    def paid_ship(self):
        return self.payment_method in {"eggs", "isk"}

    def payment_actually_taken(self):
        return not self.paid_ship() or self.payment_taken

    def needs_manual_price(self):
        return self.paid_ship() and not self.payment_taken and not self.price

    def currently_blocked(self) -> bool:
        if self.blocked_until is not None:
            return timezone.now() < self.blocked_until
        else:
            return False

    def __str__(self):
        return f"ShipOrder({self.id}) - {self.ship}*{self.quantity}->{self.recipient_character}:{self.uid}"  # type: ignore

    def availible_transitions(self):
        # pylint: disable=no-member
        return {t.name: t for t in self.get_available_state_transitions()}  # type: ignore

    def availible_transition_names(self):
        # pylint: disable=no-member
        return [t.name for t in self.get_available_state_transitions()]  # type: ignore

    @transition(field=state, source="not_started", target="inventing")
    def inventing(self):
        pass

    @transition(field=state, source="inventing", target="awaiting_production_slot")
    def awaiting_production_slot(self):
        pass

    @transition(
        field=state,
        source=["inventing", "awaiting_production_slot", "not_started"],
        target="building",
    )
    def building(self):
        pass

    @transition(field=state, source=["building", "not_started"], target="audit")
    def audit(self):
        pass

    @transition(
        field=state,
        source=["audit", "missing_contract"],
        target="waiting_on_gift_quota",
    )
    def waiting_on_gift_quota(self):
        pass

    @transition(
        field=state,
        source=["audit", "missing_contract", "not_started", "waiting_on_gift_quota"],
        target="sent",
    )
    def sent(self):
        pass

    @transition(field=state, source="audit", target="missing_contract")
    def missing_contract(self):
        pass

    @transition(field=state, source="*", target="not_started")
    def reset(self):
        pass

    class Meta:
        indexes = [models.Index(fields=["-created_at"])]
