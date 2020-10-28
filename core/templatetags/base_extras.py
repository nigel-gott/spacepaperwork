from django.db.models import Q
from django.utils import timezone

from core.models import Contract, Fleet, FleetMember, InventoryItem, MarketOrder, SoldItem, active_fleets_query, future_fleets_query, past_fleets_query
from django import template
import math as m

register = template.Library()


@register.simple_tag
def num_items(user):
    return InventoryItem.objects.filter(contract__isnull=True, location__character_location__character__discord_user=user.discord_user, quantity__gt=0).count()

@register.simple_tag
def num_orders(user):
    return MarketOrder.objects.filter(item__location__character_location__character__discord_user=user.discord_user).count()

@register.simple_tag
def num_sold(user):
    return SoldItem.objects.filter(item__location__character_location__character__discord_user=user.discord_user, transfered_to_participants=False).count()

@register.simple_tag
def can_accept_reject(user,contract):
    return contract.can_accept_or_reject(user) 

@register.simple_tag
def num_contracts (user):
    return Contract.objects.filter(to_char__discord_user=user.discord_user, status='pending').count() + Contract.objects.filter(from_user=user, status='pending').count()
@register.simple_tag
def all_sales(user):
    return sum([num_items(user), num_orders(user), num_sold(user)])

@register.simple_tag
def num_active_fleets():
    return len(active_fleets_query())


@register.simple_tag
def num_past_fleets():
    return len(past_fleets_query())

@register.filter()
def formatmoney(value):
    return m.floor(value.amount)

@register.simple_tag
def num_future_fleets():
    return len(future_fleets_query())


@register.simple_tag
def num_fleet_members(fleet_id):
    return len(FleetMember.objects.filter(fleet=fleet_id))


@register.simple_tag
def has_fleet_member(fleet, user):
    return fleet.has_member(user)


@register.simple_tag
def still_can_join_alts(fleet, user):
    return fleet.still_can_join_alts(user)

@register.simple_tag
def loot_group_still_can_join_alts(loot_group, user):
    return loot_group.still_can_join_alts(user)


@register.simple_tag
def can_join(fleet, user):
    return fleet.can_join(user)


@register.simple_tag
def has_admin(fleet, user):
    return fleet.has_admin(user)

@register.simple_tag
def has_item_admin(item, user):
    return item.has_admin(user)

@register.simple_tag
def has_share(loot_group, user):
    return loot_group.has_share(user)

@register.filter
def index(sequence, position):
    print(position)
    return sequence[position]