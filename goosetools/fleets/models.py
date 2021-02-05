from dateutil.relativedelta import relativedelta
from django import forms
from django.db import models
from django.db.models import Q
from django.utils import timezone

from goosetools.core.models import System
from goosetools.users.models import LOOT_TRACKER_ADMIN, Character, GooseUser


def human_readable_relativedelta(delta):
    attrs = ["years", "months", "days", "hours", "minutes"]
    return ", ".join(
        [
            "%d %s"
            % (getattr(delta, attr), attr if getattr(delta, attr) > 1 else attr[:-1])
            for attr in attrs
            if getattr(delta, attr)
        ]
    )


def active_fleets_query():
    now = timezone.now()
    now_minus_12_hours = now - timezone.timedelta(hours=12)
    active_fleets = Fleet.objects.filter(
        (Q(end__isnull=True) & Q(start__gte=now_minus_12_hours) & Q(start__lt=now))
        | (Q(start__lte=now) & Q(end__gt=now))
    ).order_by("-start")
    return active_fleets


def past_fleets_query():
    now = timezone.now()
    now_minus_12_hours = now - timezone.timedelta(hours=12)
    past_fleets = Fleet.objects.filter(
        (Q(end__isnull=False) & Q(end__lte=now))
        | (Q(end__isnull=True) & Q(start__lte=now_minus_12_hours))
    ).order_by("-start")
    return past_fleets


def future_fleets_query():
    now = timezone.now()
    future_fleets = Fleet.objects.filter(Q(start__gt=now)).order_by("-start")
    return future_fleets


class Fleet(models.Model):
    LOOT_TYPE_CHOICES = [
        ("Master Looter", "Master Looter"),
        ("Free For All", "Free For All"),
    ]
    fc = models.ForeignKey(GooseUser, on_delete=models.CASCADE)
    name = models.TextField()
    loot_type = models.TextField(choices=LOOT_TYPE_CHOICES, default="Master Looter")
    gives_shares_to_alts = models.BooleanField(default=False)
    start = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    expected_duration = models.TextField(blank=True, null=True)

    def members_for_user(self, user):
        return FleetMember.objects.filter(fleet=self, character__user=user)

    def has_admin(self, user):
        if user.has_perm(LOOT_TRACKER_ADMIN):
            return True
        for member in self.members_for_user(user):
            if member.admin_permissions:
                return True
        return self.fc == user

    def has_member(self, user):
        return self.members_for_user(user).count() > 0

    def is_master_looter(self):
        return self.loot_type == "Master Looter"

    def still_can_join_alts(self, user):
        num_chars = len(user.characters())
        num_characters_in_fleet = len(self.members_for_user(user))
        return (
            not self.in_the_past()
            and self.gives_shares_to_alts
            and num_characters_in_fleet > 0
            and (num_chars - num_characters_in_fleet) > 0
        )

    def is_open(self):
        now = timezone.now()
        return self.start <= now and not self.in_the_past()

    def in_the_past(self):
        now = timezone.now()
        return self.auto_end() and now >= self.auto_end()

    def can_join(self, user):
        if self.in_the_past():
            return False, "Fleet is Closed"

        num_chars = len(user.characters())
        characters_in_fleet = self.members_for_user(user)
        characters_in_fleet_display_string = ",".join(
            [fm.character.ingame_name for fm in self.members_for_user(user)]
        )
        num_characters_in_fleet = len(characters_in_fleet)

        if self.gives_shares_to_alts:
            return (
                (num_chars - num_characters_in_fleet) > 0,
                f"All Your Alts ({characters_in_fleet_display_string}) have already joined",
            )
        else:
            return (
                num_characters_in_fleet == 0,
                f"You already have one character ({characters_in_fleet_display_string}) in the fleet and you cannot join any more as the fleet doesn't allow alts.",
            )

    def member_can_be_added(self, character):
        num_chars = character.user.character_set.count()
        num_characters_in_fleet = self.fleetmember_set.filter(
            character__user=character.user
        ).count()
        if self.gives_shares_to_alts:
            return (num_chars - num_characters_in_fleet) > 0
        else:
            return num_characters_in_fleet == 0

    def human_readable_started(self):
        now = timezone.now()
        difference = self.start - now
        seconds = difference.total_seconds()
        pos_delta = relativedelta(seconds=int(abs(seconds)))
        human_delta = human_readable_relativedelta(pos_delta)
        if abs(seconds) <= 60:
            return "Starts Now"
        elif seconds > 0:
            return f"Starts in {human_delta}"
        else:
            return f"Started {human_delta} ago"

    def auto_end(self):
        now = timezone.now()
        if not self.end:
            now_minus_12_hours = now - timezone.timedelta(hours=12)
            if self.start < now_minus_12_hours:
                return self.start + timezone.timedelta(hours=12)
            else:
                return False
        else:
            return self.end

    def human_readable_ended(self):
        now = timezone.now()
        if not self.end:
            now_minus_12_hours = now - timezone.timedelta(hours=12)
            if self.start < now_minus_12_hours:
                return "Automatically expired after 12 hours"
            else:
                return False

        difference = self.end - now
        seconds = difference.total_seconds()
        pos_delta = relativedelta(seconds=int(abs(seconds)))
        human_delta = human_readable_relativedelta(pos_delta)
        if abs(seconds) <= 60:
            return "Ends Now"
        elif seconds <= 0:
            return f"Ended {human_delta} ago"
        else:
            return f"Ends in {human_delta}"

    def __str__(self):
        return str(self.name)


class FleetMember(models.Model):
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE)
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(blank=True, null=True)
    left_at = models.DateTimeField(blank=True, null=True)
    admin_permissions = models.BooleanField(default=False)

    def has_admin(self):
        return self.fleet.has_admin(self.character.user)

    class Meta:
        unique_together = (("character", "fleet"),)


class AnomType(models.Model):
    FACTIONS = [
        ("Guristas", "Guritas"),
        ("Angel", "Angel"),
        ("Blood", "Blood"),
        ("Sansha", "Sansha"),
        ("Serpentis", "Serpentis"),
        ("Asteroids", "Asteroids"),
        ("PvP", "PvP"),
    ]
    TYPE_CHOICES = [
        ("PvP Roam", "PvP Roam"),
        ("PvP Gatecamp", "PvP Gatecamp"),
        ("Deadspace", "Deadspace"),
        ("Scout", "Scout"),
        ("Inquisitor", "Inquisitor"),
        ("Condensed Belt", "Condensed Belt"),
        ("Condensed Cluster", "Condensed Cluster"),
    ]
    level = models.PositiveIntegerField()
    type = models.TextField(choices=TYPE_CHOICES)
    faction = models.TextField(choices=FACTIONS)

    def clean(self):
        if self.level < 6 and self.type == "Deadspace":
            raise forms.ValidationError("Deadspaces cannot be lower than level 6")
        if self.level < 6 and self.type.startswith("Condensed"):
            raise forms.ValidationError("Condenesed Belts cannot be lower than level 6")
        if self.type.startswith("Condensed") and self.faction != "Asteroids":
            raise forms.ValidationError("A Belt must be in the Asteroids Faction")
        if self.type.startswith("PvP") and self.faction != "PvP":
            raise forms.ValidationError("A PvP type must be in the PvP Faction")

    def __str__(self):
        return f"{self.faction} {self.type} Level {self.level}"


class FleetAnom(models.Model):
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE)
    anom_type = models.ForeignKey(AnomType, on_delete=models.CASCADE)
    time = models.DateTimeField()
    system = models.ForeignKey(System, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.anom_type} @ {self.time} in {self.system}"


class KillMail(models.Model):
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE)
    killed_ship = models.TextField()
    description = models.TextField()
    looter = models.ForeignKey(
        Character, on_delete=models.CASCADE, blank=True, null=True
    )
