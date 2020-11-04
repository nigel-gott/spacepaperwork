from decimal import Decimal
from typing import Optional, Union

from allauth.socialaccount.models import SocialAccount
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core import validators
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models, transaction
from django.db.models import DecimalField, F, FloatField, Q
from django.db.models.aggregates import Min, Sum
from django.db.models.expressions import Combinable, ExpressionWrapper
from django.db.models.fields import BooleanField
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from timezone_field import TimeZoneField
import math as m
from django.db.models.functions import Coalesce


class Corp(models.Model):
    name = models.TextField(primary_key=True)

    def __str__(self):
        return str(self.name)

# Represents a unique single person using their unique discord uid if known. They might not have ever have visited goosetools and hence will not have a GooseUser model.
class DiscordUser(models.Model):
    username = models.TextField(unique=True)
    uid = models.TextField(unique=True, blank=True, null=True)
    avatar_hash = models.TextField(blank=True, null=True)
    unknown = models.BooleanField(default=False)

    def avatar_url(self) -> Union[bool, str]: 
        return self.has_custom_avatar() and self._construct_avatar_url()
    
    # default avatars look like this: https://cdn.discordapp.com/embed/avatars/3.png 
    # there is a bug with discord's size selecting mechanism for these, doing 3.png?size=16 still returns a full size default avatar.
    def has_default_avatar(self):
        return len(str(self.avatar_hash)) == 1
    
    def has_custom_avatar(self):
        return self.avatar_hash and self.uid and not self.has_default_avatar()

    def _construct_avatar_url(self):
        return f"https://cdn.discordapp.com/avatars/{self.uid}/{self.avatar_hash}.png"
    
    def __str__(self):
        return self.username



class Character(models.Model):
    discord_user = models.ForeignKey(DiscordUser, on_delete=models.CASCADE)
    ingame_name = models.TextField(unique=True)
    corp = models.ForeignKey(Corp, on_delete=models.CASCADE)
    verified = models.BooleanField(null=True,blank=True)

    def gooseuser_or_false(self):
        return self.discord_user and hasattr(self.discord_user,'gooseuser') and self.discord_user.gooseuser

    def discord_avatar_url(self):
        return self.discord_user and self.discord_user.avatar_url()
    
    def discord_username(self):
        return self.discord_user and self.discord_user.username
        

    def __str__(self):
        return f"[{self.corp}] {self.ingame_name}"

# Add nullable discord_user FK to Character/GooseUser
# Add new Discord User Model
# Copy over character data into discord user model
# Remove nullability and old fields from models + update code

@deconstructible
class UnicodeAndSpacesUsernameValidator(UnicodeUsernameValidator):
    regex = r'^[\w.@+- ]+\Z'
    message = _(
        'Enter a valid username. This value may contain only letters, '
        'numbers, and @/./+/-/_/space  characters.'
    )
    flags = 0


class GooseUser(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[UnicodeAndSpacesUsernameValidator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    discord_user = models.OneToOneField(DiscordUser, on_delete=models.CASCADE)
    timezone = TimeZoneField(default='Europe/London')
    broker_fee = models.DecimalField(verbose_name="Your Broker Fee in %", max_digits=5, decimal_places=2, default=8.0)
    transaction_tax = models.DecimalField(verbose_name="Your Transaction Tax in %", max_digits=5, decimal_places=2, default=15.0)
    default_character = models.OneToOneField(Character, on_delete=models.CASCADE)


    def characters(self):
        if getattr(self, 'discord_user'):
            return Character.objects.filter(discord_user=self.discord_user)
        else:
            return Character.objects.none()

    def discord_uid(self):
        return self.discord_user.uid 

    def discord_username(self):
        return self.discord_user.username

    def discord_avatar_hash(self):
        return self.discord_user.uid

    def can_deposit(self):
        return SoldItem.objects.filter(item__location__character_location__character__discord_user=self.discord_user, deposited_into_eggs=False, deposit_approved=False).count() > 0
    
    def pending_deposits(self):
        return SoldItem.objects.filter(item__location__character_location__character__discord_user=self.discord_user, deposited_into_eggs=True, deposit_approved=False)
    
    def pending_transfers(self):
        return SoldItem.objects.filter(item__location__character_location__character__discord_user=self.discord_user, deposited_into_eggs=True, deposit_approved=True,transfered_to_participants=False)

    def has_pending_deposit(self):
        return self.pending_deposits().count() > 0
    def has_pending_transfers(self):
        return self.pending_transfers().count() > 0
    
    def isk_transactions(self):
        return IskTransaction.objects.filter(item__location__character_location__character__discord_user=self.discord_user)

    def egg_transactions(self):
        return EggTransaction.objects.filter(counterparty_discord_username=self.discord_username()) 
    
    def isk_balance(self):
        return to_isk(model_sum(IskTransaction.objects.filter(item__location__character_location__character__discord_user=self.discord_user), 'isk'))

    def debt_egg_balance(self):
        return to_isk(model_sum(EggTransaction.objects.filter(counterparty_discord_username=self.discord_username(), debt=True), 'eggs'))

    def egg_balance(self):
        return to_isk(model_sum(EggTransaction.objects.filter(counterparty_discord_username=self.discord_username(), debt=False), 'eggs'))


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

    def members_for_user(self, user):
        uid = user.discord_uid()
        return FleetMember.objects.filter(
            fleet=self, character__discord_user=user.discord_user)

    def has_admin(self, user):
        if user.is_staff:
            return True
        for member in self.members_for_user(user):
            if member.admin_permissions:
                return True
        return self.fc == user

    def has_member(self, user):
        return self.members_for_user(user).count() > 0

    def still_can_join_alts(self, user):
        num_chars = len(user.characters())
        num_characters_in_fleet = len(self.members_for_user(user))
        return not self.in_the_past() and self.gives_shares_to_alts and num_characters_in_fleet > 0 and (
            num_chars - num_characters_in_fleet) > 0

    def in_the_past(self):
        now = timezone.now()
        now_minus_24_hours = now - timezone.timedelta(days=1)

        return (self.end and self.end < now) or (not self.end and self.start < now_minus_24_hours)

    def can_join(self, user):
        if self.in_the_past():
            return False

        uid = user.discord_uid()
        num_chars = len(user.characters())
        num_characters_in_fleet = len(self.members_for_user(user))

        if self.gives_shares_to_alts:
            return (num_chars - num_characters_in_fleet) > 0
        else:
            return num_characters_in_fleet == 0

    def member_can_be_added(self, character):
        num_chars = len(Character.objects.filter(
             discord_user=character.discord_user))
        num_characters_in_fleet = len(FleetMember.objects.filter(
            fleet=self, character__discord_user=character.discord_user))
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
        pos_delta = relativedelta(seconds=int(abs(seconds)))
        human_delta = human_readable_relativedelta(pos_delta)
        if abs(seconds) <= 60:
            return "Ends Now"
        elif seconds <= 0:
            return f"Ended {human_delta} ago"
        else:
            return f"Ends in {human_delta}"

    def isk_and_eggs_balance(self):
        isk = to_isk(model_sum(IskTransaction.objects.filter(item__loot_group__bucket__fleet=self.id),'isk'))
        eggs = to_isk(model_sum(EggTransaction.objects.filter(item__loot_group__bucket__fleet=self.id), 'eggs'))
        return isk+eggs
    
    def estimated_profit(self):
        total = to_isk(InventoryItem.objects.filter(loot_group__fleet_anom__fleet=self.id).aggregate(estimated_profit_sum=
                    Sum(
                        Coalesce(F('item__cached_lowest_sell'), 0) * 
                        F('quantity') +
                        Coalesce(F('marketorder__listed_at_price'),0) * Coalesce(F('marketorder__quantity'),0),
                    output_field=FloatField())
                )['estimated_profit_sum'] or 0)
        return total


    def __str__(self):
        return str(self.name)


class FleetMember(models.Model):
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE)
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(blank=True, null=True)
    left_at = models.DateTimeField(blank=True, null=True)
    admin_permissions = models.BooleanField(default=False)

    def has_admin(self):
        user = self.character.gooseuser_or_false()
        if user:
            return self.fleet.has_admin(user)
        else:
            return self.admin_permissions

    class Meta:
        unique_together = (('character', 'fleet'),)


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
    eve_echoes_market_id = models.TextField(null=True,blank=True, unique=True)
    cached_lowest_sell = models.DecimalField(max_digits=20,decimal_places=2,null=True,blank=True)
    
    def latest_market_data(self):
        return self.itemmarketdataevent_set.order_by('-time').first()

    def min_of_last_x_hours(self, hours):
        time_threshold = timezone.now() - timezone.timedelta(hours=hours)
        min_price = self.itemmarketdataevent_set.filter(time__gte=time_threshold).aggregate(min_lowest_sell=Min('lowest_sell'))['min_lowest_sell']
        min_price_other = self.itemmarketdataevent_set.filter(time__gte=time_threshold).aggregate(min_sell=Min('sell'))['min_sell']
        datapoints_used = self.itemmarketdataevent_set.filter(time__gte=time_threshold).values('lowest_sell').distinct().count()
        return min_price, datapoints_used, min_price_other

    def lowest_sell(self):
        if not self.cached_lowest_sell:
            result = self.latest_market_data() and self.latest_market_data().lowest_sell
            self.cached_lowest_sell = result
        return self.cached_lowest_sell

    class Meta:
        indexes = [
            models.Index(fields=['-cached_lowest_sell']) 
        ]

    def __str__(self):
        return f"{str(self.name)}"


class ItemMarketDataEvent(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    time = models.DateTimeField()
    sell = models.DecimalField(max_digits=20,decimal_places=2,null=True,blank=True)
    buy = models.DecimalField(max_digits=20,decimal_places=2,null=True,blank=True)
    lowest_sell = models.DecimalField(max_digits=20,decimal_places=2,null=True,blank=True)
    highest_buy = models.DecimalField(max_digits=20,decimal_places=2,null=True,blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['-time']) 
        ]

    def __str__(self):
        return f"Market Price for {self.item}@{self.time}: ls={self.lowest_sell}, hb={self.highest_buy}, s={self.sell}, b={self.buy}"




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
            return f"Space On {self.character.ingame_name}({self.character.discord_username()})"
        else:
            return f"{self.system.name} On {self.character.ingame_name}({self.character.discord_username()})"


class ItemLocation(models.Model):
    character_location = models.ForeignKey(
        CharacterLocation, on_delete=models.CASCADE, blank=True, null=True)
    corp_hanger = models.ForeignKey(
        CorpHanger, on_delete=models.CASCADE, blank=True, null=True)

    def has_admin(self, user):
        # TODO support corp hanger permisions
        for char in user.characters():
            if self.character_location and self.character_location.character == char:
                return True
        return False

    def clean(self):
        if self.character_location and self.corp_hanger:
            raise ValidationError(
                _('An item cannot be located both on a character and in a corp hanger.'))
        if not self.character_location and not self.corp_hanger:
            raise ValidationError(
                _('An item must be either on a character or in a corp hanger.'))

    def in_station(self):
        return (not self.character_location) or self.character_location.system

    def __str__(self):
        if self.character_location:
            return str(self.character_location)
        else:
            return str(self.corp_hanger)

class Contract(models.Model):
    from_user = models.ForeignKey(GooseUser, on_delete=models.CASCADE, related_name='my_contracts')
    to_char = models.ForeignKey(Character, on_delete=models.CASCADE)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    created = models.DateTimeField()
    status = models.TextField(choices=[
        ("pending","pending"),
        ("rejected","rejected"),
        ("accepted","accepted"),
        ])
    log = models.JSONField(null=True,blank=True)
    
    def can_accept_or_reject(self,user):
        return self.status == 'pending' and self.to_char.gooseuser_or_false() == user

    
    def total_items(self):
        return self.inventoryitem_set.count()



class ItemFilterGroup(models.Model):
    FACTIONS = [
        ('Guristas', 'Guritas'),
        ('Angel', 'Angel'),
        ('Blood', 'Blood'),
        ('Sansha', 'Sansha'),
        ('Serpentis', 'Serpentis'),
        ('Asteroids', 'Asteroids'),
        ('PvP', 'PvP')
    ]
    TYPE_CHOICES = [
        ('PvP Roam', 'PvP Roam'),
        ('PvP Gatecamp', 'PvP Gatecamp'),
        ('Deadspace', 'Deadspace'),
        ('Scout', 'Scout'),
        ('Inquisitor', 'Inquisitor'),
        ('Condensed Belt', 'Condensed Belt'),
        ('Condensed Cluster', 'Condensed Cluster'),
    ]
    name = models.TextField(unique=True)
    anom_type = models.TextField(choices=TYPE_CHOICES, null=True, blank=True)
    faction = models.TextField(choices=FACTIONS, null=True, blank=True)
    min_level = models.PositiveIntegerField(null=True, blank=True)
    max_level = models.PositiveIntegerField(null=True, blank=True)
    def clean(self):
        if self.min_level and self.max_level and self.min_level > self.max_level: 
            raise ValidationError(_('Min level must be less than or equal to max level'))
    
    def __str__(self):
        return f"{self.name}"

class AnomType(models.Model):
    level = models.PositiveIntegerField()
    type = models.TextField(choices=ItemFilterGroup.TYPE_CHOICES)
    faction = models.TextField(choices=ItemFilterGroup.FACTIONS)

    def clean(self):
        if self.level < 6 and self.type == 'Deadspace': 
            raise ValidationError(
                _('Deadspaces cannot be lower than level 6'))
        if self.level < 6 and self.type.startswith('Condensed'):
            raise ValidationError(
                _('Condenesed Belts cannot be lower than level 6'))
        if self.type.startswith('Condensed') and self.faction != 'Asteroids':
            raise ValidationError(
                _('A Belt must be in the Asteroids Faction'))
        if self.type.startswith('PvP') and self.faction != 'PvP':
            raise ValidationError(
                _('A PvP type must be in the PvP Faction'))

    def scored_item_filter_groups(self, name_filter=None):
        groups = ItemFilterGroup.objects.filter(
            Q(faction__isnull=True) | Q(faction=self.faction) &
            Q(anom_type__isnull=True) | Q(anom_type=self.type) &
            Q(min_level__isnull=True) | Q(min_level__lte=self.level) &
            Q(max_level__isnull=True) | Q(max_level__gte=self.level) 
            )
        if name_filter:
            groups.filter(name__icontains=name_filter)
        scored_groups = [] 
        for group in groups:
            score = 0
            if group.faction:
                score = score + 10
            if group.anom_type: 
                score = score + 10
            if group.min_level and group.max_level:
                score = score + (10-(group.max_level - group.min_level))
            elif group.min_level:
                score = score + 10 - group.min_level
            elif group.max_level:
                score = score + 10 - group.max_level
            scored_groups.append((group,score))
        return sorted(scored_groups, key=lambda tup:tup[1], reverse=True)
            


    def __str__(self):
        return f"{self.faction} {self.type} Level {self.level}"



class FleetAnom(models.Model):
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE)
    anom_type = models.ForeignKey(AnomType, on_delete=models.CASCADE)
    time = models.DateTimeField()
    system = models.ForeignKey(System, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.anom_type} @ {self.time} in {self.system}"


class ItemFilter(models.Model):
    group = models.ForeignKey(ItemFilterGroup, on_delete=models.CASCADE)
    filter_type = models.TextField(choices=[
        ("exclude","exclude"),
        ("require","require"),
        ("suggest","suggest"),
    ])
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, blank=True)
    item_sub_sub_type = models.ForeignKey(ItemSubSubType, on_delete=models.CASCADE, null=True, blank=True)
    item_sub_type = models.ForeignKey(ItemSubType, on_delete=models.CASCADE, null=True, blank=True)
    item_type = models.ForeignKey(ItemType, on_delete=models.CASCADE, null=True, blank=True)


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
    def isk_and_eggs_balance(self):
        isk = to_isk(model_sum(IskTransaction.objects.filter(item__loot_group__bucket=self.id),'isk'))
        eggs = to_isk(model_sum(EggTransaction.objects.filter(item__loot_group__bucket=self.id), 'eggs'))
        return isk+eggs
    
    def total_shares(self):
        shares = LootShare.objects.filter(loot_group__bucket=self.id)
        total_shares = shares.aggregate(result=Sum('share_quantity'))['result']
        return total_shares
    
    def calculate_participation(self, isk, loot_group):
        shares = LootShare.objects.filter(loot_group__bucket=self.id)
        flat_cuts = shares.filter(loot_group=loot_group.id)
        total_shares = shares.aggregate(result=Sum('share_quantity'))['result']
        total_flat_cuts = flat_cuts.aggregate(result=Sum('flat_percent_cut'))['result']
        if total_flat_cuts is None:
            total_flat_cuts = 0
        if total_flat_cuts > 100:
            raise ValidationError(f"The Loot Group {loot_group.id} is trying to give out a total of {total_flat_cuts}% of flat cuts. Please fix the participations as this is impossible.")
        shares_by_username = shares.values('character__discord_user__username').annotate(num_shares=Sum('share_quantity'))
        flat_cuts_by_username_qs = flat_cuts.values('character__discord_user__username').annotate(flat_cut=Sum('flat_percent_cut'))
        flat_cuts_by_username = {}
        for flat_cut in flat_cuts_by_username_qs:
            flat_cuts_by_username[flat_cut['character__discord_user__username']] = flat_cut['flat_cut']
        result = {
            'total_shares':total_shares,
            'total_flat_cuts':total_flat_cuts,
            'participation':{}
        }
        total_after_cuts = isk * (100-total_flat_cuts)/100
        for group in shares_by_username:
            username= group['character__discord_user__username']
            flat_cut = flat_cuts_by_username.get(username,0)
            result['participation'][username] = {
                'shares':group['num_shares'],
                'flat_cut':flat_cut,
                'flat_cut_isk': (flat_cut/100)*isk,
                'share_isk': (group['num_shares'] / total_shares) * total_after_cuts ,
                'total_isk': (group['num_shares'] / total_shares) * total_after_cuts + (flat_cut/100)*isk,
            }
        return result



class LootGroup(models.Model):
    fleet_anom = models.ForeignKey(
        FleetAnom, on_delete=models.CASCADE, null=True, blank=True)
    killmail = models.ForeignKey(
        KillMail, on_delete=models.CASCADE, null=True, blank=True)
    bucket = models.ForeignKey(LootBucket, on_delete=models.CASCADE)
    manual = models.BooleanField(default=False)

    def total_cuts(self):
        flat_cuts = LootShare.objects.filter(loot_group=self.id)
        total_flat_cuts = flat_cuts.aggregate(result=Sum('flat_percent_cut'))['result']

    def fleet(self):
        return self.fleet_anom.fleet

    def has_admin(self,user):
        return self.fleet().has_admin(user)
    
    def has_share(self,user):
        return len(LootShare.objects.filter(
            loot_group=self,
            character__in=user.characters()
        )) > 0
    
    def alts_allowed(self):
        return self.fleet_anom.fleet.gives_shares_to_alts
    

    def can_join(self, character):
        return self.still_open() and (self.alts_allowed() or len(LootShare.objects.filter(
                loot_group=self,
                character__discord_user=character.discord_user
            )) == 0)
    
    def still_open(self):
        return not self.fleet().in_the_past()

    def still_can_join_alts(self, user):
        num_chars = len(user.characters())
        num_characters_in_group = len(LootShare.objects.filter(
            loot_group=self, character__discord_user=user.discord_user))
        return self.still_open() and self.alts_allowed() and num_characters_in_group > 0 and (
            num_chars - num_characters_in_group) > 0
            
    def isk_and_eggs_balance(self):
        isk = to_isk(model_sum(IskTransaction.objects.filter(item__loot_group=self.id),'isk'))
        eggs = to_isk(model_sum(EggTransaction.objects.filter(item__loot_group=self.id), 'eggs'))
        return isk+eggs
        
    def estimated_profit(self):
        return to_isk(InventoryItem.objects.filter(loot_group=self.id).aggregate(estimated_profit_sum=
                        Sum(
                            Coalesce(F('item__cached_lowest_sell'), 0) * 
                            (F('quantity') +
                            Coalesce(F('marketorder__quantity'),0)),
                        output_field=FloatField())
                    )['estimated_profit_sum'] or 0)
    
    def __str__(self):
        return str(self.fleet_anom) 

def model_sum(queryset, key):
    result = queryset.aggregate(result=Sum(key))['result']
    if result is None:
        return 0
    else:
        return result

def to_isk(number):
    return Money(amount=round(number,2), currency="EEI")
    
class StackedInventoryItem(models.Model):
    created_at = models.DateTimeField()

    def _first_item(self):
        items = self.inventoryitem_set.count()
        if items > 0:
            return self.inventoryitem_set.first()
        else:
            return False

    def item(self):
        return self._first_item() and self._first_item().item
    
    def marketorder(self):
        items = self.marketorders()
        if items.count() > 0:
            return items.first()
        else:
            return False
    
    def estimated_profit(self):
        lowest_sell = self._first_item() and self._first_item().item.lowest_sell()
        return lowest_sell and to_isk((self.order_quantity() + self.quantity())*lowest_sell)
    
    def order_quantity(self):
        return model_sum(MarketOrder.objects.filter(item__stack=self.id),'quantity')

    def quantity(self):
        return model_sum(InventoryItem.objects.filter(stack=self.id),'quantity')

    def sold_quantity(self):
        return model_sum(SoldItem.objects.filter(item__stack=self),'quantity')

    def total_quantity(self):
        return self.order_quantity() + self.quantity() + self.sold_quantity()
    def total_quantity_display(self):
        quantity = self.quantity()
        orders = self.order_quantity()
        sold = self.sold_quantity()
        status = ""
        if quantity > 0:
            status = status+f"{quantity} Waiting "
        if orders > 0:
            status = status+f"{orders} Selling "
        if sold > 0:
            status = status+f"{sold} Sold "
        return status 

    def buy_sell(self):
        return self.marketorder() and self.marketorder().buy_or_sell

    def internal_external(self):
        return self.marketorder() and self.marketorder().internal_or_external

    def list_price(self):
        return self.marketorder() and self.marketorder().listed_at_price

    def loc(self):
        items = self.inventoryitem_set.count()
        if items > 0:
            return self.inventoryitem_set.first().location
        else:
            return False 
    
    def items(self):
        return self.inventoryitem_set.all()

    def marketorders(self):
        return MarketOrder.objects.filter(item__stack=self.id).order_by('item__created_at')

    def has_admin(self, user):
        items = self.inventoryitem_set.count()
        if items > 0:
            return self.inventoryitem_set.first().has_admin(user)
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
    loot_group = models.ForeignKey(LootGroup, on_delete=models.SET_NULL, null=True, blank=True)
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True)
    stack = models.ForeignKey(StackedInventoryItem, on_delete=models.SET_NULL, null=True, blank=True)

    def add_isk_transaction(self, isk, transaction_type, quantity, notes, user):
        if not self.has_admin(user):
            return False, f"{user} doesn't have permissions to add an isk transaction for {self}"
        else:
            new_isk_transaction = IskTransaction(
                isk=isk,
                transaction_type=transaction_type,
                quantity=quantity,
                notes=notes,
                time=timezone.now(),
                item=self
            )
            new_isk_transaction.full_clean()
            new_isk_transaction.save()
            return True, f"Successfully added: {new_isk_transaction}"

    def has_admin(self, user):
        return self.location.has_admin(user)
    
    def status(self):
        return "Status"
    
    def isk_balance(self):
        return to_isk(model_sum(self.isktransaction_set, 'isk'))

    def egg_balance(self):
        return to_isk(model_sum(self.eggtransaction_set, 'eggs'))
    
    def isk_and_eggs_balance(self):
        return self.isk_balance()+self.egg_balance()
    
    def order_quantity(self):
        if hasattr(self, 'marketorder'): 
            return self.marketorder.quantity
        else:
            return 0

    def sold_quantity(self):
        if hasattr(self, 'solditem'): 
            return self.solditem.quantity
        else:
            return 0

    def junked_quantity(self):
        if hasattr(self, 'junkeditem'): 
            return self.junkeditem.quantity
        else:
            return 0
    
    def total_quantity(self):
        return sum([self.quantity 
        ,self.order_quantity()
        ,self.sold_quantity()
        ,self.junked_quantity()])
    
    def can_sell(self):
        return self.quantity > 0 and not self.contract
    
    def can_edit(self):
        return not hasattr(self, 'marketorder') and not hasattr(self, 'solditem') and not self.contract

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
    

    def estimated_profit(self):
        lowest_sell = self.item.lowest_sell()
        return lowest_sell and to_isk((self.quantity + self.order_quantity()) * lowest_sell)

    
    def status(self):
        status = ""
        if self.quantity != 0:
            if self.contract: 
                status = status + f" In Pending Contract"
            else:
                status = status + f" {self.quantity} Waiting"
        if self.stack:
            status = status + f" Stacked"
        quantity_listed = self.order_quantity() 
        if quantity_listed != 0:
            status = status + f" {quantity_listed} Listed"
        quantity_sold = self.sold_quantity() 
        if quantity_sold != 0:
            status = status + f" {quantity_sold} Sold ({self.solditem.status()})"
        quantity_junked = self.junked_quantity() 
        if quantity_junked != 0:
            status = status + f" {quantity_junked} Junked"
        
        esimated_profit = self.estimated_profit()
        if esimated_profit:
            status = status + f", Est Profit: {esimated_profit}"

        isk = self.isk_balance()
        if isk.amount != 0:
            status = status + f", Profit:{isk}"
        egg = self.egg_balance()
        if egg.amount != 0:
            status = status + f", Eggs Profit:{egg}"
        


        return status
    
    def __str__(self):
        return f"{self.item} x {self.total_quantity()} @ {self.location}"
    
class IskTransaction(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    time = models.DateTimeField()
    isk = MoneyField(
        max_digits=20, decimal_places=2, default_currency='EEI') 
    transaction_type = models.TextField(choices=[
        ("price_change_broker_fee", "Price Change Broker Fee"),
        ("broker_fee", "Broker Fee"),
        ("transaction_tax", "Transaction Tax"),
        ("contract_broker_fee","Contract Broker Fee"),
        ("contract_transaction_tax","Contract Transaction Tax"),
        ("contract_gross_profit", "Contract Gross Profit"),
        ("external_market_price_adjustment_fee", "InGame Market Price Adjustment Fee"),
        ("external_market_gross_profit", "InGame Market Gross Profit"),
        ("egg_deposit", "Egg Deposit"),
        ("buyback", "Buy Back"),
    ])
    notes = models.TextField(default='', blank=True)

    def __str__(self):
        return f"Isk Transaction @ {self.time} for {self.isk} of type {self.transaction_type} with notes: '{self.notes}'"

    class Meta:
        indexes = [
            models.Index(fields=['time']) 
        ]



class EggTransaction(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    time = models.DateTimeField()
    eggs = MoneyField(
        max_digits=20, decimal_places=2, default_currency='EEI') 
    debt = BooleanField(default=True)
    counterparty_discord_username = models.TextField()
    notes = models.TextField(default='', blank=True)

    def __str__(self):
        return f"{self.counterparty_discord_username} - {self.item.id} - {self.quantity} - {self.time} - {self.eggs} - Debt:{self.debt} - {self.notes}"

    class Meta:
        indexes = [
            models.Index(fields=['time']) 
        ]


class MarketOrder(models.Model):
    item = models.OneToOneField(InventoryItem, on_delete=models.CASCADE)
    internal_or_external = models.TextField(choices=[("internal", "Internal"), ("external", "External")])
    buy_or_sell = models.TextField(choices=[("buy", "Buy"), ("sell", "Sell")])
    quantity = models.PositiveIntegerField()
    listed_at_price = MoneyField(
        max_digits=20, decimal_places=2, default_currency='EEI') 
    transaction_tax = DecimalField(
        max_digits=5, decimal_places=2)
    broker_fee= DecimalField(
        max_digits=5, decimal_places=2)
    
    def has_admin(self, user):
        return self.item.has_admin(user)
    
    def change_price(self, new_price, broker_fee, changing_user):
        if not self.has_admin(changing_user):
            return False, f"You do not have permissions as {changing_user} to edit the price of {self}"
        
        with transaction.atomic():
            old_price = self.listed_at_price.amount
            if new_price == old_price:
                return False, f"The new price must be different from the old price."
            else:
                if old_price > new_price:
                    notes = f'Market Price Was Reduced from {old_price} to {new_price}'
                    fee = to_isk(m.floor(new_price * self.quantity * broker_fee/2))
                else:
                    notes = f'Market Price Was Increased from {old_price} to {new_price}'
                    fee = to_isk(m.floor((new_price - old_price/2) * self.quantity * broker_fee))
                self.listed_at_price = to_isk(new_price) 
                self.full_clean()
                self.save()
                return self.item.add_isk_transaction(-fee, "price_change_broker_fee", self.quantity, notes, changing_user)

    
    def __str__(self):
        return f"A {self.buy_or_sell} of {self.item.item} x {self.quantity} listed for {self.listed_at_price} @ {self.internal_or_external} market"


class TransferLog(models.Model):
    user = models.ForeignKey(GooseUser, on_delete=models.CASCADE)
    time = models.DateTimeField()
    explaination = models.JSONField()
    count = models.PositiveIntegerField()
    total = MoneyField(
        max_digits=20, decimal_places=2, default_currency='EEI') 

class SoldItem(models.Model):
    item = models.OneToOneField(InventoryItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    sold_via = models.TextField(choices=[("internal", "Internal Market"), ("external", "External Market"), ("contract", "Contract")])
    deposited_into_eggs = BooleanField(default=False)
    deposit_approved = BooleanField(default=False)
    transfered_to_participants = BooleanField(default=False)
    transfer_log = models.ForeignKey(TransferLog, on_delete=models.SET_NULL, null=True, blank=True)

    def isk_balance(self):
        return self.item.isk_balance()

    def isk_and_eggs_balance(self):
        return self.item.isk_and_eggs_balance()

    def status(self):
        if self.transfered_to_participants:
            return "Transfered!"
        elif self.deposited_into_eggs:
            if self.deposit_approved:
                return "Deposit Approved, Pending Transfer"
            else:
                return "Deposited Pending Approval"
        else:
            return "Pending Deposit"

    def __str__(self):
        return f"{self.item} x {self.quantity} - sold via: {self.sold_via}, status: {self.status()}"

class JunkedItem(models.Model):
    item = models.OneToOneField(InventoryItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    reason = models.TextField()


    



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
        unique_together = (('character', 'loot_group'),)

    def __str__(self):
        if self.flat_percent_cut:
            extra = f" and a {self.flat_percent_cut}% cut off the top"
        else:
            extra = ""

        return f"{self.character.discord_username} has {self.share_quantity} shares {extra}"
