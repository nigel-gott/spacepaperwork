from decimal import Decimal

from django import forms
from django.db import models
from django.db.models.aggregates import Sum
from django.db.models.expressions import Case, F, When
from django.db.models.fields import IntegerField
from django.db.models.functions import Coalesce
from django.template.defaultfilters import date as _date
from django.utils import timezone
from django.utils.datetime_safe import datetime
from django.utils.timezone import localtime
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from goosetools.fleets.models import FleetAnom, KillMail
from goosetools.users.models import Character, GooseUser
from goosetools.venmo.models import TransferMethod


def to_isk(num):
    return Money(amount=round(num, 2), currency="EEI")


def model_sum(queryset, key):
    result = queryset.aggregate(result=Sum(key))["result"]
    if result is None:
        return 0
    else:
        return result


class LootBucket(models.Model):
    def ordered_lootgroup_set(self):
        return self.lootgroup_set.order_by("-created_at").all()

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
        shares_by_user = shares.values(
            "character__user__id",
            "character__user__site_user__username",
        ).annotate(num_shares=Sum("share_quantity"))
        flat_cuts_by_user_qs = flat_cuts.values("character__user__id").annotate(
            flat_cut=Sum("flat_percent_cut")
        )
        flat_cuts_by_user = {}
        for flat_cut in flat_cuts_by_user_qs:
            flat_cuts_by_user[flat_cut["character__user__id"]] = Decimal(
                flat_cut["flat_cut"]
            )
        result = {
            "total_shares": total_shares,
            "total_flat_cuts": total_flat_cuts,
            "participation": {},
        }
        total_after_cuts = isk * Decimal(100 - total_flat_cuts) / 100
        for group in shares_by_user:
            user_id = group["character__user__id"]
            flat_cut = Decimal(flat_cuts_by_user.get(user_id, 0))
            result["participation"][user_id] = {
                "username": group["character__user__site_user__username"],
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
    character = models.OneToOneField(
        Character,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    fleet_anom = models.ForeignKey(
        FleetAnom, on_delete=models.CASCADE, null=True, blank=True
    )
    killmail = models.ForeignKey(
        KillMail, on_delete=models.CASCADE, null=True, blank=True
    )
    bucket = models.ForeignKey(LootBucket, on_delete=models.CASCADE)
    name = models.TextField(blank=True, null=True)
    manual = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    locked_participation = models.BooleanField(default=False)

    # TODO Uncouple the fleet requirement from LootGroups
    def fleet(self):
        return self.fleet_anom and self.fleet_anom.fleet

    def gooseuser_or_false(self):
        if hasattr(self, "character") and self.character:
            return self.character.user
        else:
            return False

    def display_name(self):
        if self.fleet_anom and self.fleet_anom.next_repeat:
            # noinspection PyProtectedMember
            local_start = localtime(self.fleet_anom.time)
            start = _date(local_start, "SHORT_DATE_FORMAT") + _date(local_start, " H:i")
            local_end = localtime(self.fleet_anom.next_repeat)
            if local_end.date() != local_start.date():
                prefix = _date(local_end, "SHORT_DATE_FORMAT") + " "
            else:
                prefix = ""
            end = prefix + _date(local_end, "H:i") + local_end.strftime(" %Z")
            if self.name:
                return f"{self.name} -- {start} - {end}"
            else:
                return f"{start} - {end}"
        if self.name:
            return str(self.name)
        if self.fleet_anom:
            return str(self.fleet_anom.anom_type)
        if self.gooseuser_or_false():
            return f"{self.character}'s personal items"
        else:
            return f"Loot Group {self.id}"

    def has_admin(self, user):
        gooseuser = self.gooseuser_or_false()
        return (
            self.fleet()
            and self.fleet().has_admin(user)
            or gooseuser
            and gooseuser == user
        )

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
                    loot_group=self, character__user=character.user
                )
            )
            == 0
        )

    def still_open(self):
        return not self.fleet() or (not self.fleet().in_the_past() and not self.closed)

    def still_can_join_alts(self, user):
        num_chars = len(user.characters())
        num_characters_in_group = len(
            LootShare.objects.filter(loot_group=self, character__user=user)
        )
        return (
            self.still_open()
            and self.alts_allowed()
            and num_characters_in_group > 0
            and (num_chars - num_characters_in_group) > 0
        )

    def isk_balance(self):
        return to_isk(model_sum(self.inventoryitem_set, "isktransaction__isk"))

    def non_debt_egg_balance(self):
        result = self.inventoryitem_set.aggregate(
            eggs=Sum(
                Case(
                    When(
                        eggtransaction__debt=False,
                        then=F("eggtransaction__eggs"),
                    ),
                    output_field=IntegerField(),
                    default=0,
                )
            )
        )["eggs"]
        if result is None:
            return to_isk(0)
        else:
            return to_isk(result)

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

    @staticmethod
    def create_or_get_personal(character):
        if hasattr(character, "lootgroup"):
            return character.lootgroup
        else:
            bucket = LootBucket.objects.create()
            loot_group = LootGroup.objects.create(
                character=character, bucket=bucket, locked_participation=True
            )
            LootShare.objects.create(
                loot_group=loot_group,
                character=character,
                share_quantity=1,
                created_at=datetime.now(),
            )
            return loot_group

    def __str__(self):
        return self.display_name()


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

        return f"{self.character.user.display_name()} has {self.share_quantity} shares {extra}"


class TransferLog(models.Model):
    user = models.ForeignKey(GooseUser, on_delete=models.CASCADE)
    time = models.DateTimeField()
    explaination = models.JSONField()  # type: ignore
    count = models.PositiveIntegerField()
    total = MoneyField(max_digits=20, decimal_places=2, default_currency="EEI")
    own_share = MoneyField(
        max_digits=20, decimal_places=2, default_currency="EEI", blank=True, null=True
    )
    new_transfer_method = models.ForeignKey(
        TransferMethod, on_delete=models.SET_NULL, null=True, blank=True
    )
    # The old method, please use the new one above!
    transfer_method = models.TextField(null=True, blank=True)
    deposit_command = models.TextField(default="", blank=True)
    transfer_command = models.TextField(default="", blank=True)
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
