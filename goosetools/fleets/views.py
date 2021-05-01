import math
from typing import Dict, List

from django.contrib import messages
from django.db import transaction
from django.db.models import Case, Sum
from django.db.models.expressions import F, When
from django.db.models.fields import IntegerField
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls.base import reverse
from django.utils import timezone

from goosetools.fleets.models import (
    Fleet,
    FleetMember,
    active_fleets_query,
    future_fleets_query,
    past_fleets_query,
)
from goosetools.ownership.models import LootBucket, LootGroup
from goosetools.ownership.views import generate_fleet_profit
from goosetools.users.models import Character

from .forms import FleetAddMemberForm, FleetForm, JoinFleetForm


def forbidden(request):
    messages.error(request, "You are forbidden to access this.")
    return render(request, "core/403.html")


def fleet_list_view(request, fleets_to_display, page_url_name):
    page = int(request.GET.get("page", 0))
    page_size = 20
    total_pages = math.floor(fleets_to_display.count() / page_size)
    this_page_fleets = fleets_to_display[page * page_size : (page + 1) * page_size]
    header = "Active Fleets"
    if page_url_name == "fleet_past":
        header = "Past Fleets"
    elif page_url_name == "fleet_future":
        header = "Future Fleets"

    fleets_annotated_with_isk_and_eggs_balance = this_page_fleets.annotate(
        isk_and_eggs_balance=Sum(
            Case(
                When(
                    fleetanom__lootgroup__inventoryitem__eggtransaction__debt=False,
                    then=F("fleetanom__lootgroup__inventoryitem__eggtransaction__eggs"),
                ),
                output_field=IntegerField(),
                default=0,
            )
        )
    )
    context = {
        "page_url_name": page_url_name,
        "fleets": fleets_annotated_with_isk_and_eggs_balance,
        "header": header,
        "page": page,
        "total_pages": total_pages,
        "total_pages_range": range(total_pages),
    }
    return render(request, "fleets/fleet.html", context)


def all_fleets_view(request):
    active_fleets = active_fleets_query()
    return fleet_list_view(request, active_fleets, "all_fleets_view")


def fleet_past(request):
    past_fleets = past_fleets_query()
    return fleet_list_view(request, past_fleets, "fleet_past")


def fleet_future(request):
    future_fleets = future_fleets_query()
    return fleet_list_view(request, future_fleets, "fleet_future")


def fleet_leave(request, pk):
    member = get_object_or_404(FleetMember, pk=pk)
    fleet = member.fleet
    if member.character.user == request.gooseuser or fleet.has_admin(request.gooseuser):
        member.delete()
    else:
        messages.error(
            request, "You do not have permissions to remove that member from the fleet"
        )
    return HttpResponseRedirect(reverse("fleet_view", args=[fleet.pk]))


def fleet_view(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    fleet_members = f.fleetmember_set.all()
    by_user: Dict[int, List[FleetMember]] = {}
    for member in fleet_members:
        if member.character.user.id not in by_user:
            by_user[member.character.user.id] = []
        by_user[member.character.user.id].append(member)
    loot_buckets = (
        LootBucket.objects.filter(lootgroup__fleet_anom__fleet=f)
        .prefetch_related("lootgroup_set")
        .all()
    )
    return render(
        request,
        "fleets/fleet_view.html",
        {
            "fleet": f,
            "fleet_members_by_id": by_user,
            "loot_buckets": loot_buckets,
        },
    )


@transaction.atomic
def fleet_open(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    if f.has_admin(request.gooseuser):
        if not f.is_open():
            f.end = None
            f.start = timezone.now()
            f.full_clean()
            f.save()
        else:
            messages.error(request, "You cannot open an already open fleet")
    else:
        return forbidden(request)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@transaction.atomic
def fleet_end(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    if f.has_admin(request.gooseuser):
        if f.is_open():
            f.end = timezone.now()
            f.full_clean()
            f.save()
            LootGroup.objects.filter(bucket__lootgroup__fleet_anom__fleet=f).update(
                closed=True
            )
        else:
            messages.error(
                request, "You cannot end a future fleet or one that is already closed."
            )
    else:
        return forbidden(request)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def fleet_make_admin(request, pk):
    f = get_object_or_404(FleetMember, pk=pk)
    if f.fleet.has_admin(request.gooseuser):
        f.admin_permissions = True
        f.full_clean()
        f.save()
    else:
        return forbidden(request)
    return HttpResponseRedirect(reverse("fleet_view", args=[f.fleet.pk]))


def fleet_remove_admin(request, pk):
    f = get_object_or_404(FleetMember, pk=pk)
    if f.fleet.has_admin(request.gooseuser):
        f.admin_permissions = False
        f.full_clean()
        f.save()
    else:
        return forbidden(request)
    return HttpResponseRedirect(reverse("fleet_view", args=[f.fleet.pk]))


def fleet_add(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    if not f.has_admin(request.gooseuser):
        return forbidden(request)
    if request.method == "POST":
        form = FleetAddMemberForm(request.POST)
        if form.is_valid():
            character = form.cleaned_data["character"]
            if f.member_can_be_added(character):
                new_fleet_member = FleetMember(
                    character=character, fleet=f, joined_at=timezone.now()
                )
                new_fleet_member.full_clean()
                new_fleet_member.save()
            else:
                messages.error(request, "You cannot add an alt to this fleet")
            return HttpResponseRedirect(reverse("fleet_view", args=[pk]))
    else:
        form = FleetAddMemberForm(initial={"fleet": f.id})
    existing_members = f.fleetmember_set.values("character__id")
    form.fields["character"].queryset = Character.objects.exclude(
        id__in=existing_members
    )
    return render(request, "fleets/add_fleet_form.html", {"form": form, "fleet": f})


def fleet_join(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    if request.method == "POST":
        form = JoinFleetForm(request.POST)
        if form.is_valid():
            can_join, error_message = f.can_join(request.gooseuser)
            if can_join:
                new_fleet = FleetMember(
                    character=form.cleaned_data["character"],
                    fleet=f,
                    joined_at=timezone.now(),
                )
                new_fleet.full_clean()
                new_fleet.save()
                return HttpResponseRedirect(reverse("fleet_view", args=[pk]))
            else:
                messages.error(request, f"Error Joining Fleet: {error_message}")
                return HttpResponseRedirect(reverse("fleet_view", args=[pk]))
    else:
        form = JoinFleetForm(initial={"character": request.gooseuser.default_character})
    characters = non_member_chars(pk, request.gooseuser)
    form.fields["character"].queryset = characters

    return render(request, "fleets/join_fleet_form.html", {"form": form, "fleet": f})


def non_member_chars(fleet_id, user):
    existing = FleetMember.objects.filter(fleet=fleet_id).values("character")
    characters = Character.objects.filter(user=user).exclude(pk__in=existing)
    return characters


def fleet_create(request):
    if request.method == "POST":
        form = FleetForm(request.POST)
        if form.is_valid():
            combined_start = timezone.make_aware(
                timezone.datetime.combine(
                    form.cleaned_data["start_date"], form.cleaned_data["start_time"]
                )
            )
            combined_end = None
            if form.cleaned_data["end_date"]:
                combined_end = timezone.make_aware(
                    timezone.datetime.combine(
                        form.cleaned_data["end_date"], form.cleaned_data["end_time"]
                    )
                )

            if combined_end and combined_end <= combined_start:
                messages.error(
                    request,
                    "The fleet start time must be before the fleet end time!",
                )
            else:
                new_fleet = Fleet(
                    fc=request.gooseuser,
                    loot_type=form.cleaned_data["loot_type"],
                    name=form.cleaned_data["name"],
                    description=form.cleaned_data["description"],
                    location=form.cleaned_data["location"],
                    expected_duration=form.cleaned_data["expected_duration"],
                    gives_shares_to_alts=form.cleaned_data["gives_shares_to_alts"],
                    start=combined_start,
                    end=combined_end,
                )
                new_fleet.full_clean()
                new_fleet.save()

                fc_member = FleetMember(
                    character=form.cleaned_data["fc_character"],
                    fleet=new_fleet,
                    joined_at=timezone.now(),
                    admin_permissions=True,
                )
                fc_member.full_clean()
                fc_member.save()
                return HttpResponseRedirect(reverse("fleet_view", args=[new_fleet.pk]))

    else:
        now = timezone.localtime(timezone.now())
        form = FleetForm(
            initial={
                "start_date": now.date(),
                "start_time": now.time(),
                "fc_character": request.gooseuser.default_character,
            }
        )

        form.fields["fc_character"].queryset = request.gooseuser.characters()

    return render(
        request, "fleets/fleet_form.html", {"form": form, "title": "Create Fleet"}
    )


def fleet_edit(request, pk):
    existing_fleet = Fleet.objects.get(pk=pk)
    if not existing_fleet.has_admin(request.gooseuser):
        return forbidden(request)
    if request.method == "POST":
        form = FleetForm(request.POST)
        if form.is_valid():
            combined_start = timezone.make_aware(
                timezone.datetime.combine(
                    form.cleaned_data["start_date"], form.cleaned_data["start_time"]
                )
            )
            combined_end = None
            if form.cleaned_data["end_date"]:
                combined_end = timezone.make_aware(
                    timezone.datetime.combine(
                        form.cleaned_data["end_date"], form.cleaned_data["end_time"]
                    )
                )

            if combined_end and combined_end <= combined_start:
                messages.error(
                    request,
                    "The fleet start time must be before the fleet end time!",
                )
            else:
                existing_fleet.fc = existing_fleet.fc
                existing_fleet.loot_type = form.cleaned_data["loot_type"]
                existing_fleet.name = form.cleaned_data["name"]
                existing_fleet.description = form.cleaned_data["description"]
                existing_fleet.location = form.cleaned_data["location"]
                existing_fleet.start = combined_start
                existing_fleet.end = combined_end
                existing_fleet.expected_duration = form.cleaned_data[
                    "expected_duration"
                ]
                existing_fleet.gives_shares_to_alts = form.cleaned_data[
                    "gives_shares_to_alts"
                ]
                existing_fleet.full_clean()
                existing_fleet.save()
                return HttpResponseRedirect(reverse("fleet_view", args=[pk]))

    else:
        form = FleetForm(
            initial={
                "start_date": existing_fleet.start.date(),
                "start_time": existing_fleet.start.time(),
                "end_date": existing_fleet.end and existing_fleet.end.date(),
                "end_time": existing_fleet.end and existing_fleet.end.time(),
                "loot_type": existing_fleet.loot_type,
                "name": existing_fleet.name,
                "description": existing_fleet.description,
                "location": existing_fleet.location,
                "expected_duration": existing_fleet.expected_duration,
                "gives_shares_to_alts": existing_fleet.gives_shares_to_alts,
            }
        )
        form.fields["fc_character"].queryset = existing_fleet.fc.characters()

    return render(
        request, "fleets/fleet_form.html", {"form": form, "title": "Edit Fleet"}
    )


def fleet_profit(request, pk):
    existing_fleet = Fleet.objects.get(pk=pk)
    stats = generate_fleet_profit(existing_fleet)
    return render(
        request,
        "fleets/fleet_profit.html",
        {"fleet": existing_fleet, "title": "Fleet", "stats": stats},
    )
