from django.utils.translation import gettext_lazy as _

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from djmoney.models.fields import MoneyField
from timezone_field import TimeZoneField
from dateutil.relativedelta import relativedelta


class GooseUser(AbstractUser):
    timezone = TimeZoneField(default='Europe/London')

    def discord_uid(self):
        if len(self.socialaccount_set.all()) == 0:
            return 0
        else:
            return self.socialaccount_set.only()[0].uid

    def discord_username(self):
        social_account = self.socialaccount_set.only()[0].extra_data
        return f"@{social_account['username']}#{social_account['discriminator']}"

    def characters(self):
        return Character.objects.filter(discord_id=self.discord_uid())

    def discord_avatar_url(self):
        """
        :return: Returns the users discord avatar image link or false if they do not have one or an error occurs.
        """
        try:
            social_infos = SocialAccount.objects.filter(user=self)
            if len(social_infos) == 1:
                social_info = social_infos[0]
                avatar_hash = social_info.extra_data['avatar']
                discord_id = social_info.uid
                return f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png"
        except Exception:
            pass
        return False


class Region(models.Model):
    name = models.TextField(primary_key=True)

    def __str__(self):
        return str(self.name)


class System(models.Model):
    name = models.TextField(primary_key=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    jumps_to_jita = models.PositiveIntegerField(null=True, blank=True)
    security = models.TextField()

    def __str__(self):
        return f"{self.name} ({self.region} , {self.security})"


class Corp(models.Model):
    name = models.TextField(primary_key=True)

    def __str__(self):
        return str(self.name)


class Character(models.Model):
    discord_id = models.TextField()
    ingame_name = models.TextField()
    discord_avatar_url = models.TextField()
    discord_username = models.TextField()
    corp = models.ForeignKey(Corp, on_delete=models.CASCADE)

    def user_or_false(self):
        try:
            return SocialAccount.objects.get(uid=self.discord_id).user
        except ObjectDoesNotExist:
            return False

    def __str__(self):
        return f"[{self.corp}] {self.ingame_name}"


class FleetType(models.Model):
    type = models.TextField()
    material_icon = models.TextField()
    material_colour = models.TextField()

    def __str__(self):
        return str(self.type)


def human_readable_relativedelta(delta):
    attrs = ['years', 'months', 'days', 'hours', 'minutes']
    return ', '.join(
        ['%d %s' % (getattr(delta, attr), attr if getattr(delta, attr) > 1 else attr[:-1]) for attr in attrs if
         getattr(delta, attr)])


def active_fleets_query():
    now = timezone.now()
    now_minus_24_hours = now - timezone.timedelta(days=1)
    active_fleets = \
        Fleet.objects.filter(
            (Q(end__isnull=True) & Q(start__gte=now_minus_24_hours) & Q(start__lt=now)) | (Q(start__lte=now) &
                                                                                           Q(end__gt=now))).order_by(
            '-start')
    return active_fleets


def past_fleets_query():
    now = timezone.now()
    now_minus_24_hours = now - timezone.timedelta(days=1)
    past_fleets = \
        Fleet.objects.filter(
            (Q(end__isnull=False) & Q(end__lte=now)) | (
                    Q(end__isnull=True) & Q(start__lte=now_minus_24_hours))).order_by('-start')
    return past_fleets


def future_fleets_query():
    now = timezone.now()
    future_fleets = \
        Fleet.objects.filter(
            Q(start__gt=now)).order_by('-start')
    return future_fleets


class Fleet(models.Model):
    fc = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.TextField()
    fleet_type = models.ForeignKey(FleetType, on_delete=models.CASCADE)
    gives_shares_to_alts = models.BooleanField(default=False)
    start = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    expected_duration = models.TextField(blank=True, null=True)

    def has_admin(self, user):
        uid = user.discord_uid()
        members = FleetMember.objects.filter(fleet=self, character__discord_id=uid)
        if user.is_staff:
            return True
        for member in members:
            if member.admin_permissions:
                return True
        return self.fc == user

    def has_member(self, user):
        uid = user.discord_uid()
        num_characters_in_fleet = len(FleetMember.objects.filter(fleet=self, character__discord_id=uid))
        return num_characters_in_fleet > 0

    def still_can_join_alts(self, user):
        uid = user.discord_uid()
        num_chars = len(Character.objects.filter(discord_id=user.discord_uid()))
        num_characters_in_fleet = len(FleetMember.objects.filter(fleet=self, character__discord_id=uid))
        return not self.in_the_past() and self.gives_shares_to_alts and num_characters_in_fleet > 0 and (
                num_chars - num_characters_in_fleet) > 0

    def in_the_past(self):
        now = timezone.now()
        now_minus_24_hours = now - timezone.timedelta(days=1)

        return (self.end and self.end < now) or (not self.end and self.start < now_minus_24_hours)

    def can_join(self, user):
        if self.in_the_past():
            print("Past")
            return False

        uid = user.discord_uid()
        num_chars = len(Character.objects.filter(discord_id=user.discord_uid()))
        num_characters_in_fleet = len(FleetMember.objects.filter(fleet=self, character__discord_id=uid))

        if self.gives_shares_to_alts:
            return (num_chars - num_characters_in_fleet) > 0
        else:
            return num_characters_in_fleet == 0

    def human_readable_started(self):
        now = timezone.now()
        difference = self.start - now
        seconds = difference.total_seconds()
        pos_delta = relativedelta(seconds=abs(seconds))
        human_delta = human_readable_relativedelta(pos_delta)
        if abs(seconds) <= 60:
            return "Starts Now"
        elif seconds > 0:
            return f"Starts in {human_delta}"
        else:
            return f"Started {human_delta} ago"

    def human_readable_ended(self):
        now = timezone.now()
        if not self.end:
            now_minus_24_hours = now - timezone.timedelta(days=1)
            if self.start < now_minus_24_hours:
                return "Automatically expired after 24 hours"
            else:
                return False

        difference = self.end - now
        seconds = difference.total_seconds()
        pos_delta = relativedelta(seconds=abs(seconds))
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


class ItemType(models.Model):
    name = models.TextField()

    def __str__(self):
        return str(self.name)


class ItemSubType(models.Model):
    item_type = models.ForeignKey(ItemType, on_delete=models.CASCADE)
    name = models.TextField()

    def __str__(self):
        return f"{self.item_type} -> {str(self.name)}"


class ItemSubSubType(models.Model):
    item_sub_type = models.ForeignKey(ItemSubType, on_delete=models.CASCADE)
    name = models.TextField()

    def __str__(self):
        return f"{self.item_sub_type} -> {str(self.name)}"


class Item(models.Model):
    item_type = models.ForeignKey(ItemSubSubType, on_delete=models.CASCADE)
    name = models.TextField(primary_key=True)

    def __str__(self):
        return f"{str(self.name)}"


class Station(models.Model):
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    name = models.TextField(primary_key=True)


class CorpHanger(models.Model):
    corp = models.ForeignKey(Corp, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    hanger = models.CharField(max_length=1, choices=[
        ('1', 'Hanger 1'),
        ('2', 'Hanger 2'),
        ('3', 'Hanger 3'),
        ('4', 'Hanger 4'),
    ])

    def __str__(self):
        return f"In [{self.corp.name}] Corp {self.hanger} at {self.station} ({self.character.discord_username}"


class CharacterLocation(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        if not self.station:
            return f"In Space on {self.character.ingame_name}({self.character.discord_username})"
        else:
            return f"In {self.character.ingame_name}'s personal hanger at {self.station} ({self.character.discord_username}"


class ItemLocation(models.Model):
    character_location = models.ForeignKey(CharacterLocation, on_delete=models.CASCADE, blank=True, null=True)
    corp_hanger = models.ForeignKey(CorpHanger, on_delete=models.CASCADE, blank=True, null=True)

    def clean(self):
        if self.character_location and self.corp_hanger:
            raise ValidationError(_('An item cannot be located both on a character and in a corp hanger.'))
        if not self.character_location and not self.corp_hanger:
            raise ValidationError(_('An item must be either on a character or in a corp hanger.'))

    def in_station(self):
        return (not self.character_location) or self.character_location.station

    def __str__(self):
        if self.character_location:
            return str(self.character_location)
        else:
            return str(self.corp_hanger)


class AnomType(models.Model):
    TYPE_CHOICES = [
        ('Deadspace', 'Deadspace'),
        ('Scout', 'Scout'),
        ('Inquisitor', 'Inquisitor'),
        ('Condensed Belt', 'Condensed Belt'),
        ('Condensed Cluster', 'Condensed Cluster'),
    ]
    FACTIONS = [
        ('Guristas', 'Guritas'),
        ('Angel','Angel'),
        ('Blood', 'Blood'),
        ('Sansha', 'Sansha'),
        ('Serpentis', 'Serpentis'),
        ('Asteroids', 'Asteroids')
    ]
    level = models.PositiveIntegerField()
    type = models.TextField(choices=TYPE_CHOICES)
    faction = models.TextField(choices=FACTIONS)

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
        Character,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )


class LootBucket(models.Model):
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE)


class LootGroup(models.Model):
    fleet_anom = models.ForeignKey(FleetAnom, on_delete=models.CASCADE, null=True, blank=True)
    killmail = models.ForeignKey(KillMail, on_delete=models.CASCADE, null=True, blank=True)
    bucket = models.ForeignKey(LootBucket, on_delete=models.CASCADE)
    manual = models.BooleanField(default=False)

    def fleet(self):
        return self.fleet_anom.fleet


class InventoryItem(models.Model):
    location = models.ForeignKey(ItemLocation, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveBigIntegerField()
    remaining_quantity = models.PositiveIntegerField()
    listed_at_price = MoneyField(max_digits=14, decimal_places=2, default_currency='EEI', null=True, blank=True)
    total_profit = MoneyField(max_digits=14, decimal_places=2, default_currency='EEI', null=True, blank=True)
    loot_group = models.ForeignKey(LootGroup, on_delete=models.CASCADE)

    def status(self):
        if self.quantity > self.remaining_quantity:
            if self.listed_at_price:
                return "Listed"
            elif self.location.in_station():
                return "Waiting"
            else:
                return "Transit"
        else:
            return "All Sold"


    def __str__(self):
        if self.status() == "All Sold":
            extra = f" - sold for total profit of {self.total_profit}"
        elif self.listed_at_price:
            extra = f" - listed @ {self.listed_at_price} for total {self.listed_at_price * self.quantity}"
        else:
            extra = ""
        return f"{self.item} x {self.quantity} @ {self.location} {extra}"


class LootShare(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    loot_group = models.ForeignKey(LootGroup, on_delete=models.CASCADE)
    share_quantity = models.PositiveIntegerField(default=0)
    flat_percent_cut = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (('character', 'loot_group'),)

    def __str__(self):
        if self.flat_percent_cut:
            extra = f" and a {self.flat_percent_cut}% cut off the top"
        else:
            extra = ""

        return f"{self.character.discord_username} has {self.share_quantity} shares {extra}"
