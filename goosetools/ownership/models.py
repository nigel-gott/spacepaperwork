from decimal import Decimal

from django import forms
from django.db import models
from django.db.models.aggregates import Sum
from django.db.models.expressions import F
from django.db.models.functions import Coalesce
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from goosetools.fleets.models import Fleet, FleetAnom, KillMail
from goosetools.users.models import Character, GooseUser


def to_isk(num):
    return Money(amount=round(num, 2), currency="EEI")


def model_sum(queryset, key):
    result = queryset.aggregate(result=Sum(key))["result"]
    if result is None:
        return 0
    else:
        return result


class LootBucket(models.Model):
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE)

    def isk_and_eggs_balance(self):
        isk = to_isk(
            model_sum(self.lootgroup_set, "inventoryitem__item__isktransaction__isk")
        )
        eggs = to_isk(
            model_sum(self.lootgroup_set, "inventoryitem__item__eggtransaction__eggs")
        )
        return isk + eggs

    def total_shares(self):
        shares = LootShare.objects.filter(loot_group__bucket=self.id)
        total_shares = shares.aggregate(result=Sum("share_quantity"))["result"]
        return total_shares

    def calculate_participation(self, isk, loot_group):
        shares = LootShare.objects.filter(loot_group__bucket=self.id)
        flat_cuts = shares.filter(loot_group=loot_group.id)
        total_shares = shares.aggregate(result=Sum("share_quantity"))["result"]
        total_flat_cuts = flat_cuts.aggregate(result=Sum("flat_percent_cut"))["result"]
        if total_flat_cuts is None:
            total_flat_cuts = 0
        if total_flat_cuts > 100:
            raise forms.ValidationError(
                f"The Loot Group {loot_group.id} is trying to give out a total of {total_flat_cuts}% of flat cuts. Please fix the participations as this is impossible."
            )
        shares_by_username = shares.values(
            "character__discord_user__username"
        ).annotate(num_shares=Sum("share_quantity"))
        flat_cuts_by_username_qs = flat_cuts.values(
            "character__discord_user__username"
        ).annotate(flat_cut=Sum("flat_percent_cut"))
        flat_cuts_by_username = {}
        for flat_cut in flat_cuts_by_username_qs:
            flat_cuts_by_username[
                flat_cut["character__discord_user__username"]
            ] = Decimal(flat_cut["flat_cut"])
        result = {
            "total_shares": total_shares,
            "total_flat_cuts": total_flat_cuts,
            "participation": {},
        }
        total_after_cuts = isk * Decimal(100 - total_flat_cuts) / 100
        for group in shares_by_username:
            username = group["character__discord_user__username"]
            flat_cut = Decimal(flat_cuts_by_username.get(username, 0))
            result["participation"][username] = {
                "shares": group["num_shares"],
                "flat_cut": flat_cut,
                "flat_cut_isk": (flat_cut / 100) * isk,
                "share_isk": (Decimal(group["num_shares"]) / total_shares)
                * total_after_cuts,
                "total_isk": (Decimal(group["num_shares"]) / total_shares)
                * total_after_cuts
                + (flat_cut / 100) * isk,
            }
        return result


class LootGroup(models.Model):
    fleet_anom = models.ForeignKey(
        FleetAnom, on_delete=models.CASCADE, null=True, blank=True
    )
    killmail = models.ForeignKey(
        KillMail, on_delete=models.CASCADE, null=True, blank=True
    )
    bucket = models.ForeignKey(LootBucket, on_delete=models.CASCADE)
    name = models.TextField(blank=True, null=True)
    manual = models.BooleanField(default=False)

    # TODO Uncouple the fleet requirement from LootGroups
    def fleet(self):
        return self.fleet_anom and self.fleet_anom.fleet

    def display_name(self):
        if self.name:
            return self.name
        if self.fleet_anom:
            return self.fleet_anom.anom_type
        else:
            return f"Loot Group {self.id}"

    def has_admin(self, user):
        return self.fleet() and self.fleet().has_admin(user)

    def has_share(self, user):
        return (
            len(
                LootShare.objects.filter(
                    loot_group=self, character__in=user.characters()
                )
            )
            > 0
        )

    def alts_allowed(self):
        return self.fleet_anom and self.fleet_anom.fleet.gives_shares_to_alts

    def can_join(self, character):
        return self.still_open() and (
            self.alts_allowed()
            or len(
                LootShare.objects.filter(
                    loot_group=self, character__discord_user=character.discord_user
                )
            )
            == 0
        )

    def still_open(self):
        return not self.fleet().in_the_past()

    def still_can_join_alts(self, user):
        num_chars = len(user.characters())
        num_characters_in_group = len(
            LootShare.objects.filter(
                loot_group=self, character__discord_user=user.discord_user
            )
        )
        return (
            self.still_open()
            and self.alts_allowed()
            and num_characters_in_group > 0
            and (num_chars - num_characters_in_group) > 0
        )

    def isk_and_eggs_balance(self):
        isk = to_isk(model_sum(self.inventoryitem_set, "isktransaction__isk"))
        eggs = to_isk(model_sum(self.inventoryitem_set, "eggtransaction__eggs"))
        return isk + eggs

    def estimated_profit(self):
        return to_isk(
            self.inventoryitem_set.aggregate(
                estimated_profit_sum=Sum(
                    Coalesce(F("item__cached_lowest_sell"), 0)
                    * (F("quantity") + Coalesce(F("marketorder__quantity"), 0)),
                    output_field=models.FloatField(),
                )
            )["estimated_profit_sum"]
            or 0
        )

    def __str__(self):
        return str(self.fleet_anom)


class LootShare(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    loot_group = models.ForeignKey(LootGroup, on_delete=models.CASCADE)
    share_quantity = models.PositiveIntegerField(default=0)
    flat_percent_cut = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField()

    def has_admin(self, user):
        return self.loot_group.has_admin(user)

    def increment(self):
        self.share_quantity = self.share_quantity + 1
        self.full_clean()
        self.save()

    def decrement(self):
        self.share_quantity = self.share_quantity - 1
        if self.share_quantity <= 0:
            self.delete()
        else:
            self.full_clean()
            self.save()

    class Meta:
        unique_together = (("character", "loot_group"),)

    def __str__(self):
        if self.flat_percent_cut:
            extra = f" and a {self.flat_percent_cut}% cut off the top"
        else:
            extra = ""

        return f"{self.character.discord_username} has {self.share_quantity} shares {extra}"


class TransferLog(models.Model):
    user = models.ForeignKey(GooseUser, on_delete=models.CASCADE)
    time = models.DateTimeField()
    explaination = models.JSONField()  # type: ignore
    count = models.PositiveIntegerField()
    total = MoneyField(max_digits=20, decimal_places=2, default_currency="EEI")
    own_share = MoneyField(
        max_digits=20, decimal_places=2, default_currency="EEI", blank=True, null=True
    )
    deposit_command = models.TextField(default="")
    transfer_command = models.TextField(default="")
    own_share_in_eggs = models.BooleanField(default=True)
    all_done = models.BooleanField(default=True)
    legacy_transfer = models.BooleanField(default=True)

    def other_peoples_share(self):
        return self.total - self.own_share

    def safe_own_share(self):
        if self.own_share is None:
            return 0
        else:
            return self.own_share

    def egg_deposit_amount(self):
        if self.own_share_in_eggs:
            return self.total
        else:
            return self.total - self.safe_own_share()
