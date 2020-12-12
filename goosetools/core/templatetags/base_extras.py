import math as m
import numbers

from django import template
from django.db.models.expressions import F

from goosetools.contracts.models import Contract
from goosetools.fleets.models import (
    FleetMember,
    active_fleets_query,
    future_fleets_query,
    past_fleets_query,
)
from goosetools.items.models import InventoryItem
from goosetools.market.models import MarketOrder, SoldItem
from goosetools.users.models import CorpApplication, UserApplication

register = template.Library()


@register.simple_tag
def num_items(user):
    return InventoryItem.objects.filter(
        contract__isnull=True,
        location__character_location__character__discord_user=user.discord_user,
        quantity__gt=0,
    ).count()


@register.simple_tag
def num_orders(user):
    return MarketOrder.objects.filter(
        item__location__character_location__character__discord_user=user.discord_user
    ).count()


@register.simple_tag
def num_sold(user):
    return SoldItem.objects.filter(
        item__location__character_location__character__discord_user=user.discord_user,
        transfered_quantity__lt=F("quantity"),
    ).count()


@register.simple_tag
def can_accept_reject(user, contract):
    return contract.can_accept_or_reject(user)


@register.simple_tag
def num_contracts(user):
    return (
        Contract.objects.filter(
            to_char__discord_user=user.discord_user, status="pending"
        ).count()
        + Contract.objects.filter(from_user=user, status="pending").count()
    )


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


@register.filter()
def nicemoney(value):
    if isinstance(value, numbers.Number):
        floored = m.floor(value)  # type: ignore
    elif value is None:
        floored = 0
    else:
        floored = m.floor(value.amount)

    if floored > 1000000000000:
        return str(round(floored / 1000000000000, 2)) + "T"
    if floored > 1000000000:
        return str(round(floored / 1000000000, 2)) + "B"
    if floored > 1000000:
        return str(round(floored / 1000000, 2)) + "M"
    if floored > 1000:
        return str(round(floored / 1000, 2)) + "K"
    return floored


@register.simple_tag
def num_future_fleets():
    return len(future_fleets_query())


@register.simple_tag
def num_pending_user_apps():
    return UserApplication.unapproved_applications().count()


@register.simple_tag
def num_pending_corp_apps():
    return CorpApplication.unapproved_applications().count()


@register.simple_tag
def num_pending_apps():
    return num_pending_corp_apps() + num_pending_user_apps()


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
    can_join_fleet, _ = fleet.can_join(user)
    return can_join_fleet


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
    return sequence[position]
