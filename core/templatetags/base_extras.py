from django.db.models import Q
from django.utils import timezone

from core.models import Fleet, FleetMember
from django import template

register = template.Library()


def active_fleets_query():
    now = timezone.now()
    now_minus_24_hours = now - timezone.timedelta(days=1)
    active_fleets = \
        Fleet.objects.filter(
            Q(start__gte=now_minus_24_hours) & Q(start__lte=now) & (Q(end__gt=now) | Q(end__isnull=True))).order_by(
            '-start')
    return active_fleets


@register.simple_tag
def num_active_fleets():
    return len(active_fleets_query())


@register.simple_tag
def num_fleet_members(fleet_id):
    return len(FleetMember.objects.filter(fleet=fleet_id))


@register.simple_tag
def has_fleet_member(fleet, user):
    return fleet.has_member(user)
