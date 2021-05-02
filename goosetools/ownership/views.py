import json
import math as m
from decimal import Decimal
from typing import Dict, List

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import F, Sum
from django.db.models.aggregates import Count
from django.db.models.functions import Coalesce
from django.forms.formsets import formset_factory
from django.http.response import HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.safestring import mark_safe
from djmoney.money import Money
from moneyed.localization import format_money

from goosetools.bank.models import EggTransaction, IskTransaction
from goosetools.contracts.models import Contract
from goosetools.core.models import System
from goosetools.fleets.models import AnomType, Fleet, FleetAnom
from goosetools.items.forms import InventoryItemForm
from goosetools.items.models import CharacterLocation, InventoryItem, ItemLocation
from goosetools.market.models import SoldItem
from goosetools.ownership.forms import (
    LootGroupForm,
    LootJoinForm,
    LootShareForm,
    TransferProfitForm,
)
from goosetools.ownership.models import (
    LootBucket,
    LootGroup,
    LootShare,
    TransferLog,
    to_isk,
)
from goosetools.users.forms import CharacterForm
from goosetools.users.models import Character, GooseUser


class ComplexEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Money):
            return format_money(o, locale=translation.get_language())
        if isinstance(o, Decimal):
            return str(m.floor(o))
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, o)


# Two types needed - one without bucket which makes it, one which adds group to existing bucket
# Buckets group up all shares in underlying groups and split all items in underlying groups by total shares
def loot_group_create(request, pk):
    f = get_object_or_404(Fleet, pk=pk)
    if not f.has_admin(request.user.gooseuser):
        return forbidden(request)
    return loot_group_add(request, pk, False)


def non_participation_chars(loot_group, user):
    existing = LootShare.objects.filter(
        loot_group=loot_group, character__user=user
    ).values("character")
    return user.characters().exclude(pk__in=existing)


def forbidden(request):
    messages.error(request, "You are forbidden to access this.")
    return render(request, "ownership/403.html")


def raise_if_locked(request, loot_group):
    if loot_group.locked_participation:
        message = f"Cannot modify the locked group: {loot_group}"
        messages.error(request, message)
        raise Exception(message)


def loot_share_join(request, pk):
    loot_group = get_object_or_404(LootGroup, pk=pk)

    raise_if_locked(request, loot_group)
    if request.method == "POST":
        form = LootJoinForm(request.POST)
        if form.is_valid():
            selected_character = form.cleaned_data["character"]
            if selected_character not in request.user.gooseuser.characters():
                messages.error(
                    request,
                    f"{selected_character} is not your Character, you cannot join the loot group with it.",
                )
            elif not loot_group.can_join(selected_character):
                messages.error(
                    request, f"{selected_character} is not allowed to join this group."
                )
            else:
                ls = LootShare(
                    character=selected_character,
                    loot_group=loot_group,
                    share_quantity=1,
                    flat_percent_cut=0,
                    created_at=timezone.now(),
                )
                ls.full_clean()
                ls.save()
            return HttpResponseRedirect(reverse("loot_group_view", args=[pk]))
    else:
        can_still_join = non_participation_chars(loot_group, request.user.gooseuser)
        if len(can_still_join) == 0:
            messages.error(
                request,
                "You have no more characters that can join this loot group. Don't worry you have probably already been added check below to make sure!",
            )
            return HttpResponseRedirect(reverse("loot_group_view", args=[pk]))
        if loot_group.has_share(
            request.user.gooseuser
        ) and not loot_group.still_can_join_alts(request.user.gooseuser):
            messages.error(
                request,
                "You cannot join with more characters as the fleet doesn't allow alts to have shares.",
            )
            return HttpResponseRedirect(reverse("loot_group_view", args=[pk]))
        default_char = request.user.gooseuser.default_character
        if default_char not in can_still_join:
            default_char = can_still_join[0]
        form = LootJoinForm(initial={"character": default_char})
        form.fields["character"].queryset = can_still_join
    return render(
        request,
        "ownership/loot_join_form.html",
        {"form": form, "title": "Add Your Participation", "loot_group": loot_group},
    )


def loot_share_add(request, pk):
    loot_group = get_object_or_404(LootGroup, pk=pk)
    if not loot_group.has_admin(request.user.gooseuser):
        return forbidden(request)
    raise_if_locked(request, loot_group)
    if request.method == "POST":
        form = LootShareForm(request.POST)
        if form.is_valid():
            character = form.cleaned_data["character"]
            ls = LootShare(
                character=character,
                loot_group=loot_group,
                share_quantity=form.cleaned_data["share_quantity"],
                flat_percent_cut=form.cleaned_data["flat_percent_cut"],
                created_at=timezone.now(),
            )
            ls.full_clean()
            ls.save()
            return HttpResponseRedirect(reverse("loot_group_view", args=[pk]))
    else:
        form = LootShareForm(initial={"share_quantity": 1, "flat_percent_cut": 0})
    return render(
        request,
        "ownership/loot_share_form.html",
        {"form": form, "title": "Add New Loot Share"},
    )


def loot_share_delete(request, pk):
    loot_share = get_object_or_404(LootShare, pk=pk)
    if not loot_share.has_admin(request.gooseuser):
        return forbidden(request)
    raise_if_locked(request, loot_share.loot_group)
    if request.method == "POST":
        group_pk = loot_share.loot_group.pk
        loot_share.delete()
        return HttpResponseRedirect(reverse("loot_group_view", args=[group_pk]))
    else:
        return forbidden(request)


def loot_share_edit(request, pk):
    loot_share = get_object_or_404(LootShare, pk=pk)
    if not loot_share.has_admin(request.gooseuser):
        return forbidden(request)
    raise_if_locked(request, loot_share.loot_group)
    if request.method == "POST":
        form = LootShareForm(request.POST)
        if form.is_valid():
            loot_share.character = form.cleaned_data["character"]
            loot_share.share_quantity = form.cleaned_data["share_quantity"]
            loot_share.flat_percent_cut = form.cleaned_data["flat_percent_cut"]
            loot_share.full_clean()
            loot_share.save()
            return HttpResponseRedirect(
                reverse("loot_group_view", args=[loot_share.loot_group.pk])
            )
    else:
        form = LootShareForm(
            initial={
                "share_quantity": loot_share.share_quantity,
                "flat_percent_cut": loot_share.flat_percent_cut,
                "character": loot_share.character,
            }
        )
    return render(
        request,
        "ownership/loot_share_form.html",
        {"form": form, "title": "Edit Loot Share"},
    )


def loot_share_add_fleet_members(request, pk):
    loot_group = get_object_or_404(LootGroup, pk=pk)
    raise_if_locked(request, loot_group)
    if request.method == "POST":
        for fleet_member in loot_group.fleet_anom.fleet.fleetmember_set.all():  # type: ignore
            LootShare.objects.get_or_create(
                character=fleet_member.character,
                loot_group=loot_group,
                defaults={
                    "share_quantity": 1,
                    "flat_percent_cut": 0,
                    "created_at": timezone.now(),
                },
            )
    return HttpResponseRedirect(reverse("loot_group_view", args=[pk]))


def loot_group_close(request, pk):
    loot_group = get_object_or_404(LootGroup, pk=pk)
    raise_if_locked(request, loot_group)
    if not loot_group.has_admin(request.user.gooseuser):
        return forbidden(request)
    if request.method == "POST":
        loot_group.closed = True
        if loot_group.fleet_anom:
            loot_group.fleet_anom.minute_repeat_period = None
            loot_group.fleet_anom.save()
        loot_group.full_clean()
        loot_group.save()
        messages.success(request, f"Closed loot group: {loot_group}")
        return HttpResponseRedirect(reverse("loot_group_view", args=[loot_group.id]))
    else:
        return HttpResponseNotAllowed("POST")


def loot_group_open(request, pk):
    loot_group = get_object_or_404(LootGroup, pk=pk)
    if not loot_group.has_admin(request.user.gooseuser):
        return forbidden(request)
    raise_if_locked(request, loot_group)
    if request.method == "POST":
        loot_group.closed = False
        loot_group.full_clean()
        loot_group.save()
        messages.success(request, f"Opened loot group: {loot_group}")
        return HttpResponseRedirect(reverse("loot_group_view", args=[loot_group.id]))
    else:
        return HttpResponseNotAllowed("POST")


class WrongFleetBucketException(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message


def loot_group_add(request, fleet_pk, loot_bucket_pk):
    f = get_object_or_404(Fleet, pk=fleet_pk)
    if request.method == "POST":
        form = LootGroupForm(request.POST)
        if form.is_valid():
            # Form will let you specify anom/km/other
            # depending on mode, a anom/km/other info will be created
            # also can come with participation filled in and items filled in all on one form
            try:
                spawned = timezone.now()
                loot_source = form.cleaned_data["loot_source"]
                anom_level = form.cleaned_data["anom_level"]
                a_type = form.cleaned_data["anom_type"]
                anom_faction = form.cleaned_data["anom_faction"]
                system = form.cleaned_data["anom_system"]
                name = form.cleaned_data["name"]
                next_repeat = calc_next_repeat(form, spawned)
                minute_repeat_period = form.cleaned_data["minute_repeat_period"]
                new_group = loot_group_create_internal(
                    f,
                    loot_source,
                    anom_level,
                    a_type,
                    anom_faction,
                    loot_bucket_pk,
                    spawned,
                    system,
                    name,
                    minute_repeat_period,
                    next_repeat,
                    0,
                )
                return HttpResponseRedirect(
                    reverse("loot_group_view", args=[new_group.id])
                )
            except WrongFleetBucketException as e:
                messages.error(request, e.message)
                return HttpResponseRedirect(reverse("fleet_view", args=[f.id]))
    else:
        form = LootGroupForm()

    return render(
        request,
        "ownership/loot_group_form.html",
        {"form": form, "title": "Start New Loot Group"},
    )


def calc_next_repeat(form, spawned):
    minute_repeat_period = form.cleaned_data["minute_repeat_period"]
    if minute_repeat_period:
        next_repeat = spawned + timezone.timedelta(minutes=minute_repeat_period)
        return next_repeat
    else:
        return None


def loot_group_create_internal(
    f,
    loot_source,
    anom_level,
    a_type,
    anom_faction,
    loot_bucket_pk,
    spawned,
    system,
    name,
    minute_repeat_period,
    next_repeat,
    repeat_count,
):
    if loot_source == LootGroupForm.ANOM_LOOT_GROUP:
        anom_type = AnomType.objects.get_or_create(
            level=anom_level,
            type=a_type,
            faction=anom_faction,
        )[0]
        anom_type.full_clean()
        anom_type.save()
        if not loot_bucket_pk:
            loot_bucket = LootBucket()
            loot_bucket.save()
        else:
            loot_bucket = get_object_or_404(LootBucket, pk=loot_bucket_pk)
            num_groups_for_this_fleet = loot_bucket.lootgroup_set.filter(
                fleet_anom__fleet=f
            ).count()
            if num_groups_for_this_fleet != loot_bucket.lootgroup_set.count():
                raise WrongFleetBucketException(
                    "You cannot add a fleet anom to this "
                    "bucket as this bucket is not for "
                    "this fleet.",
                )

        fleet_anom = FleetAnom(
            fleet=f,
            anom_type=anom_type,
            time=spawned,
            system=system,
            next_repeat=next_repeat,
            minute_repeat_period=minute_repeat_period,
            repeat_count=repeat_count,
        )
        fleet_anom.full_clean()
        fleet_anom.save()

        new_group = LootGroup(
            name=name,
            bucket=loot_bucket,
            fleet_anom=fleet_anom,
            created_at=timezone.now(),
        )
        new_group.full_clean()
        new_group.save()
        return new_group
    else:
        return None


def loot_group_edit(request, pk):
    loot_group = get_object_or_404(LootGroup, pk=pk)
    fleet_anom = loot_group.fleet_anom
    if not fleet_anom:
        raise Exception(f"Missing fleet anom for {loot_group}")
    raise_if_locked(request, loot_group)
    if request.method == "POST":
        form = LootGroupForm(request.POST)
        if form.is_valid():
            loot_group.name = form.cleaned_data["name"]

            # todo handle more loot sources?
            if form.cleaned_data["loot_source"] == LootGroupForm.ANOM_LOOT_GROUP:
                fleet_anom.anom_type = AnomType.objects.get_or_create(
                    level=form.cleaned_data["anom_level"],
                    type=form.cleaned_data["anom_type"],
                    faction=form.cleaned_data["anom_faction"],
                )[0]
                fleet_anom.system = form.cleaned_data["anom_system"]
                fleet_anom.next_repeat = calc_next_repeat(form, timezone.now())
                fleet_anom.minute_repeat_period = form.cleaned_data[
                    "minute_repeat_period"
                ]
                fleet_anom.full_clean()
                fleet_anom.save()

            loot_group.full_clean()
            loot_group.save()

            return HttpResponseRedirect(reverse("loot_group_view", args=[pk]))

    else:
        form = LootGroupForm(
            initial={
                "name": loot_group.name,
                "anom_system": fleet_anom.system,
                "anom_level": fleet_anom.anom_type.level,
                "anom_faction": fleet_anom.anom_type.faction,
                "anom_type": fleet_anom.anom_type.type,
                "start_repeating_at": fleet_anom.next_repeat.time()
                if fleet_anom.next_repeat
                else None,
                "minute_repeat_period": fleet_anom.minute_repeat_period,
            }
        )

    return render(
        request,
        "ownership/loot_group_form.html",
        {"form": form, "title": "Edit Loot Group"},
    )


def loot_group_view(request, pk):
    loot_group = get_object_or_404(LootGroup, pk=pk)
    by_user: Dict[int, List[LootShare]] = {}
    for loot_share in loot_group.lootshare_set.all():
        user_id = loot_share.character.user.id
        if user_id not in by_user:
            by_user[user_id] = []
        by_user[user_id].append(loot_share)

    if loot_group.gooseuser_or_false():
        add_url = reverse("personal_items_add")
    else:
        add_url = reverse("item_add", args=[loot_group.pk])
    return render(
        request,
        "ownership/loot_group_view.html",
        {
            "loot_group": loot_group,
            "loot_shares_by_user_id": by_user,
            "item_add_url": add_url,
        },
    )


def your_fleet_shares(request):
    return fleet_shares(request, request.user.gooseuser.pk)


def fleet_shares(request, pk):
    loot_shares = LootShare.objects.filter(character__user_id=pk)
    items = []
    seen_groups = {}
    all_your_estimated_share_isk = 0
    all_your_real_share_isk = 0
    your_total_est_sales = 0

    user = GooseUser.objects.get(pk=pk)
    for_you = user == request.user.gooseuser
    if for_you:
        prefix = "Your"
        prefix2 = "Your"
    else:
        prefix = f"{user.discord_username()}'s"
        prefix2 = "Their"

    for loot_share in loot_shares:
        loot_group = loot_share.loot_group
        if loot_group.id in seen_groups:
            continue
        seen_groups[loot_group.id] = True

        my_items = InventoryItem.objects.filter(
            location__character_location__character__user=user,
            loot_group=loot_group,
        )
        estimated_profit = 0
        for item in my_items:
            estimated_profit = estimated_profit + (item.estimated_profit() or 0)
        your_total_est_sales = estimated_profit + your_total_est_sales
        total_estimated_profit = loot_group.estimated_profit()
        real_profit = loot_group.non_debt_egg_balance()
        estimated_participation = loot_group.bucket.calculate_participation(
            total_estimated_profit, loot_group
        )
        real_participation = loot_group.bucket.calculate_participation(
            real_profit, loot_group
        )
        your_group_estimated_profit = estimated_participation["participation"][user.id][
            "total_isk"
        ]
        your_real_profit = real_participation["participation"][user.id]["total_isk"]
        items.append(
            {
                "username": user.discord_username(),
                "fleet_id": loot_group.fleet_anom.fleet.id
                if loot_group.fleet_anom
                else False,
                "loot_bucket": loot_group.bucket.id,
                "loot_group_id": loot_group.id,
                "your_shares": estimated_participation["participation"][user.id][
                    "shares"
                ],
                "your_cut": estimated_participation["participation"][user.id][
                    "flat_cut"
                ],
                "total_shares": estimated_participation["total_shares"],
                "total_cuts": estimated_participation["total_flat_cuts"],
                "my_estimated_profit": estimated_profit,
                "group_estimated_profit": total_estimated_profit,
                "your_group_estimated_profit": your_group_estimated_profit,
                "group_real_profit": real_profit,
                "your_real_profit": your_real_profit,
                "item_count": my_items.count(),
            }
        )
        all_your_estimated_share_isk = (
            all_your_estimated_share_isk + your_group_estimated_profit
        )
        all_your_real_share_isk = all_your_real_share_isk + your_real_profit
    items = sorted(items, key=lambda x: x["loot_bucket"])
    return render(
        request,
        "ownership/your_fleets_view.html",
        {
            "prefix": prefix,
            "prefix2": prefix2,
            "sales_est": your_total_est_sales,
            "all_est": all_your_estimated_share_isk,
            "all_real": all_your_real_share_isk,
            "items": items,
            "title": f"{prefix} Fleet Share Summary",
        },
    )


def loot_share_plus(request, pk):
    loot_share = get_object_or_404(LootShare, pk=pk)
    if not loot_share.has_admin(request.user.gooseuser):
        return forbidden(request)
    raise_if_locked(request, loot_share.loot_group)
    if request.method == "POST":
        loot_share.increment()
    return HttpResponseRedirect(
        reverse("loot_group_view", args=[loot_share.loot_group.id])
    )


def loot_share_minus(request, pk):
    loot_share = get_object_or_404(LootShare, pk=pk)
    if not loot_share.has_admin(request.user.gooseuser):
        return forbidden(request)
    raise_if_locked(request, loot_share.loot_group)
    if request.method == "POST":
        loot_share.decrement()
    return HttpResponseRedirect(
        reverse("loot_group_view", args=[loot_share.loot_group.id])
    )


def transfered_items(request):
    characters = request.user.gooseuser.characters()
    all_sold = []
    for char in characters:
        char_locs = CharacterLocation.objects.filter(character=char)
        for char_loc in char_locs:
            loc = ItemLocation.objects.get(
                character_location=char_loc, corp_hanger=None
            )
            done = SoldItem.objects.filter(
                item__location=loc, quantity=F("transfered_quantity")
            )
            all_sold.append({"loc": loc, "done": done})

    return render(request, "ownership/transfered_items.html", {"all_sold": all_sold})


def completed_profit_transfers(request):
    return render(
        request,
        "ownership/completed_egg_transfers.html",
        {
            "transfer_logs": request.user.gooseuser.transferlog_set.filter(
                all_done=True
            )
            .order_by("-time")
            .all()
        },
    )


def view_transfer_log(request, pk):
    item = get_object_or_404(TransferLog, pk=pk)
    return render(
        request,
        "ownership/view_transfer_log.html",
        {"log": item, "explaination": json.loads(item.explaination)},
    )


def generate_contract_requests(
    total_participation,
    transfering_user: GooseUser,
    character_with_profit: Character,
    transfer,
):
    command = f"Your loot has been sold!\n Please send a contract in-game to '{character_with_profit.ingame_name}' for the amount of ISK you are owed shown below:\n\n"
    deposit_total = 0
    for user_id, isk in total_participation.items():
        floored_isk = m.floor(isk.amount)
        if user_id != transfering_user.id:
            user = GooseUser.objects.get(id=user_id)
            command = command + f"<@!{user.discord_uid()}> {floored_isk} \n"

            Contract.create(
                user,
                character_with_profit,
                System.objects.first(),
                "requested",
                -floored_isk,
                transfer,
            )

            deposit_total = deposit_total + floored_isk
    return deposit_total, command


def make_transfer_command(total_participation, transfering_user: GooseUser):
    if settings.USE_NEW_VENMO_COMMANDS:
        command = "/bulk transfer: "
    else:
        command = "$bulk\n"
    length_since_last_bulk = len(command)
    commands_issued = False
    deposit_total = 0
    for user_id, isk in total_participation.items():
        floored_isk = m.floor(isk.amount)
        if user_id != transfering_user.id:
            user = GooseUser.objects.get(id=user_id)
            commands_issued = True
            if settings.USE_NEW_VENMO_COMMANDS:
                next_user = f"<@!{user.discord_uid()}> {floored_isk} "
            else:
                next_user = f"<@{user.discord_uid()}> {floored_isk}\n"
            if length_since_last_bulk + len(next_user) > 1500:
                if settings.USE_NEW_VENMO_COMMANDS:
                    new_bulk = "/bulk transfer: "
                else:
                    new_bulk = "$bulk\n"
                command = (
                    command
                    + "\nNEW MESSAGE TO AVOID DISCORD CHARACTER LIMIT:\n"
                    + new_bulk
                )
                length_since_last_bulk = len(new_bulk)

            command = command + next_user
            length_since_last_bulk = length_since_last_bulk + len(next_user)
            deposit_total = deposit_total + floored_isk
    if not commands_issued:
        command = "no one to transfer to"
    return command


def make_deposit_command(others_share, own_share, own_share_in_eggs, left_over):
    if own_share_in_eggs:
        deposit = others_share + own_share + left_over
    else:
        deposit = others_share
    if settings.USE_NEW_VENMO_COMMANDS:
        return f"/deposit amount: {int(deposit.amount)}"
    else:
        return f"$deposit {int(deposit.amount)}"


def transfer_sold_items(
    to_transfer, own_share_in_eggs, request, transfer_method, contract_character
):
    total = 0
    sellers_isk = to_isk(0)
    others_isk = to_isk(0)
    left_over = to_isk(0)
    count = 0
    total_participation: Dict[str, Decimal] = {}
    explaination = {}
    current_now = timezone.now()
    last_item = None
    for sold_item in to_transfer:
        last_item = sold_item.item
        quantity_to_transfer = sold_item.quantity_to_transfer()
        total_isk = to_isk(sold_item.isk_balance)
        bucket = sold_item.item.loot_group.bucket
        participation = bucket.calculate_participation(
            total_isk, sold_item.item.loot_group
        )
        item_id = sold_item.item.id
        explaination[item_id] = participation
        explaination[item_id]["item"] = str(sold_item.item)
        explaination[item_id]["total_isk"] = total_isk.amount
        explaination[item_id]["transfered_quantity"] = quantity_to_transfer
        total = total + total_isk
        count = count + quantity_to_transfer
        for user_id, result in participation["participation"].items():
            user = GooseUser.objects.get(id=user_id)
            isk = result["total_isk"]
            floored_isk = to_isk(m.floor(isk.amount))
            if request.user.gooseuser == user:
                sellers_isk = sellers_isk + floored_isk
            else:
                others_isk = others_isk + floored_isk
            left_over = left_over + isk - floored_isk

            deposit_transaction = IskTransaction(
                item=sold_item.item,
                quantity=quantity_to_transfer,
                time=current_now,
                isk=-floored_isk,
                transaction_type="egg_deposit",
            )
            deposit_transaction.full_clean()
            deposit_transaction.save()
            egg_transaction = EggTransaction(
                item=sold_item.item,
                quantity=quantity_to_transfer,
                time=current_now,
                eggs=floored_isk,
                debt=False,
                counterparty=user,
            )
            egg_transaction.full_clean()
            egg_transaction.save()
            if user_id in total_participation:
                total_participation[user_id] = (
                    total_participation[user_id] + floored_isk
                )
            else:
                total_participation[user_id] = floored_isk
        sold_item.transfered_quantity = sold_item.quantity
        sold_item.full_clean()
        sold_item.save()

    left_over_floored = to_isk(m.floor(left_over.amount))
    if left_over.amount > 0:
        if last_item is None:
            raise Exception(
                "Error trying to transfer 0 sold items somehow so nothing to attach leftovers onto"
            )
        item_to_attach_left_overs_onto = last_item
        IskTransaction.objects.create(
            item=item_to_attach_left_overs_onto,
            quantity=0,
            time=current_now,
            isk=-left_over,
            transaction_type="fractional_remains",
            notes="Fractional leftovers assigned to the loot seller ",
        )
        if left_over_floored.amount > 0:
            EggTransaction.objects.create(
                item=item_to_attach_left_overs_onto,
                quantity=0,
                time=current_now,
                eggs=left_over_floored,
                debt=False,
                counterparty=request.user.gooseuser,
                notes="Fractional leftovers assigned to the loot seller ",
            )

    transfer_command = ""
    deposit_command = ""
    if transfer_method == "eggs":
        deposit_command = make_deposit_command(
            others_isk, sellers_isk, own_share_in_eggs, left_over
        )
        transfer_command = make_transfer_command(
            total_participation, request.user.gooseuser
        )
        messages.success(
            request,
            f"Generated Deposit and Transfer commands for {total} eggs from {count} sold items!.",
        )
    log = TransferLog(
        user=request.user.gooseuser,
        time=timezone.now(),
        total=total,
        own_share=sellers_isk,
        count=count,
        explaination=json.dumps(explaination, cls=ComplexEncoder),
        transfer_command=transfer_command,
        deposit_command=deposit_command,
        all_done=False,
        legacy_transfer=False,
        own_share_in_eggs=own_share_in_eggs,
        transfer_method=transfer_method,
    )
    log.full_clean()
    log.save()
    if transfer_method == "contract":
        t, text = generate_contract_requests(
            total_participation, request.gooseuser, contract_character, log
        )
        log.transfer_command = text
        log.save()
        messages.success(
            request,
            f"Told all recipients to Send {contract_character} contracts in-game for {t} ISK from {count} sold items!.",
        )
    to_transfer.update(transfer_log=log.id)
    return log.id


def valid_transfer(to_transfer, request, form):
    if to_transfer.count() == 0:
        messages.error(request, "You cannot transfer 0 items")
        return False

    if (
        form.cleaned_data["transfer_method"] == "contract"
        and not form.cleaned_data["character_to_send_contracts_to"]
    ):
        error_message = "You must specify a character which people will be sending the contracts to get their profit"
        messages.error(request, mark_safe(error_message))
        return False

    loot_groups = to_transfer.values("item__loot_group").distinct()
    invalid_groups = (
        LootGroup.objects.filter(id__in=loot_groups)
        .annotate(
            share_sum=Coalesce(
                Sum(F("lootshare__share_quantity") + F("lootshare__flat_percent_cut")),
                0,
            )
        )
        .filter(share_sum__lte=0)
    )
    if len(invalid_groups) > 0:
        error_message = "The following loot groups you are attempting to transfer isk for have no participation at all, you must first setup some participation for these groups before you can deposit isk:"
        for invalid_group in invalid_groups:
            error_message = (
                error_message
                + f"<br/> *  <a href='{reverse('loot_group_view', args=[invalid_group.pk])}'>{invalid_group}</a> "
            )
        messages.error(request, mark_safe(error_message))
        return False

    negative_items = list(to_transfer.filter(isk_balance__lt=0).all())
    if len(negative_items) > 0:
        error_message = "You are trying to transfer an item which has made a negative profit, something has probably gone wrong please PM @thejanitor immediately."
        for sold_item in negative_items:
            error_message = (
                error_message
                + f"<br/> *  <a href='{reverse('item_view', args=[sold_item.item.pk])}'>{sold_item}</a> "
            )
        messages.error(request, mark_safe(error_message))
        return False

    return True


@transaction.atomic
def transfer_profit(request):
    if request.method == "POST":
        form = TransferProfitForm(request.POST)
        form.fields[
            "character_to_send_contracts_to"
        ].queryset = request.gooseuser.characters()

        if form.is_valid():
            to_transfer = SoldItem.objects.filter(
                item__location__character_location__character__user=request.gooseuser,
                quantity__gt=F("transfered_quantity"),
            ).annotate(isk_balance=Sum("item__isktransaction__isk"))
            if not valid_transfer(to_transfer, request, form):
                return HttpResponseRedirect(reverse("sold"))
            log_id = transfer_sold_items(
                to_transfer,
                form.cleaned_data["own_share_in_eggs"],
                request,
                form.cleaned_data["transfer_method"],
                form.cleaned_data["character_to_send_contracts_to"],
            )
            if log_id:
                return HttpResponseRedirect(reverse("view_transfer_log", args=[log_id]))
            else:
                return HttpResponseRedirect(reverse("sold"))
    else:
        form = TransferProfitForm(
            initial={
                "character_to_send_contracts_to": request.user.gooseuser.default_character
            }
        )
        form.fields[
            "character_to_send_contracts_to"
        ].queryset = request.gooseuser.characters()
    return render(
        request,
        "ownership/transfer_profit.html",
        {"form": form, "title": "Transfer Profit"},
    )


@transaction.atomic
def mark_transfer_as_done(request, pk):
    log = get_object_or_404(TransferLog, pk=pk)
    if request.method == "POST":
        if log.user != request.user.gooseuser:
            messages.error(request, "You cannot mark someone else's transfer as done.")
            return HttpResponseRedirect(reverse("sold"))
        else:
            log.all_done = True
            log.full_clean()
            log.save()
            return HttpResponseRedirect(reverse("sold"))
    else:
        return HttpResponseNotAllowed("POST")


def personal_items_add(request):
    return add_items_internal(
        request,
        10,
        LootGroup.create_or_get_personal,
        "Add New Personal Items",
        reverse("items"),
        reverse("personal_items_add"),
    )


def item_add(request, lg_pk):
    loot_group = get_object_or_404(LootGroup, pk=lg_pk)
    if not loot_group.has_admin(request.gooseuser):
        return forbidden(request)
    return add_items_internal(
        request,
        10,
        lambda _: loot_group,
        "Add New Items to Loot Group " + loot_group.display_name(),
        reverse("loot_group_view", args=[loot_group.pk]),
        reverse("item_add", args=[loot_group.pk]),
    )


def add_items_internal(
    request, extra, loot_group_getter, title, success_redirect, item_add_url
):
    initial = [{"quantity": 1} for _ in range(0, extra)]
    InventoryItemFormset = formset_factory(InventoryItemForm, extra=0)  # noqa
    if request.method == "POST":
        formset = InventoryItemFormset(request.POST, request.FILES, initial=initial)
        char_form = CharacterForm(request.POST)
        char_form.fields["character"].queryset = request.user.gooseuser.characters()
        if formset.is_valid() and char_form.is_valid():
            character = char_form.cleaned_data["character"]
            loot_group = loot_group_getter(character)
            count = 0
            for form in formset:
                item_type = form.cleaned_data["item"]
                quantity = form.cleaned_data["quantity"]
                if item_type and quantity:
                    char_loc = CharacterLocation.objects.get_or_create(
                        character=character, system=None
                    )
                    loc = ItemLocation.objects.get_or_create(
                        character_location=char_loc[0], corp_hanger=None
                    )
                    items = InventoryItem.objects.filter(
                        location=loc[0],
                        loot_group=loot_group,
                        item=item_type,
                    )
                    if items.exists():
                        created = False
                        item = items.last()
                    else:
                        item = InventoryItem.objects.create(
                            location=loc[0],
                            loot_group=loot_group,
                            item=item_type,
                            quantity=quantity,
                            created_at=timezone.now(),
                        )
                        created = True

                    count = count + quantity
                    if not created:
                        if item.can_edit():
                            item.quantity = item.quantity + quantity
                            item.full_clean()
                            item.save()
                        else:
                            new_item = InventoryItem(
                                location=loc[0],
                                loot_group=loot_group,
                                item=item_type,
                                quantity=quantity,
                                created_at=timezone.now(),
                            )
                            new_item.full_clean()
                            new_item.save()
            add_another = request.POST.get("add_another", False)
            if add_another:
                messages.success(request, f"Added {count} items")
                return HttpResponseRedirect(request.get_full_path())
            else:
                return HttpResponseRedirect(success_redirect)
    else:
        char_form = CharacterForm(
            initial={"character": request.user.gooseuser.default_character}
        )
        char_form.fields["character"].queryset = request.user.gooseuser.characters()
        formset = InventoryItemFormset(initial=initial)
    return render(
        request,
        "ownership/loot_item_form.html",
        {
            "formset": formset,
            "char_form": char_form,
            "title": title,
            "item_add_url": item_add_url,
        },
    )


def generate_fleet_profit(fleet):
    by_user = {}
    by_user_by_bucket = {}
    total_item_shares_per_bucket = {}
    total_shares = 0
    bucket_info = {}

    all_fleet_buckets = (
        LootBucket.objects.filter(lootgroup__fleet_anom__fleet=fleet).distinct().all()
    )
    for bucket in all_fleet_buckets:
        all_bucket_items = InventoryItem.objects.filter(loot_group__bucket=bucket)
        total_items_in_bucket = all_bucket_items.count()

        total_item_shares_per_bucket[bucket.id] = bucket.total_shares()
        shares = LootShare.objects.filter(loot_group__bucket=bucket)
        groups_with_shares = (
            LootGroup.objects.annotate(shares=Sum("lootshare__share_quantity"))
            .filter(bucket=bucket, shares__gt=0)
            .count()
        )
        groups_with_items = (
            LootGroup.objects.annotate(items=Count("inventoryitem"))
            .filter(bucket=bucket, items__gt=0)
            .count()
        )
        bucket_info.setdefault(bucket.id, {})
        bucket_info[bucket.id]["groups_with_shares"] = groups_with_shares
        bucket_info[bucket.id]["groups_with_items"] = groups_with_items
        bucket_info[bucket.id]["total_items"] = total_items_in_bucket
        bucket_info[bucket.id]["real_profit"] = to_isk(0)
        bucket_info[bucket.id]["est_profit"] = to_isk(0)

        for loot_group in bucket.lootgroup_set.all():
            bucket_info[bucket.id]["est_profit"] += loot_group.estimated_profit()
            bucket_info[bucket.id]["real_profit"] += loot_group.non_debt_egg_balance()

        for share in shares:
            user = share.character.user
            shares = share.share_quantity
            by_user.setdefault(user.id, 0)
            by_user_by_bucket.setdefault(user.id, {})
            total_item_shares_per_bucket.setdefault(bucket.id, 0)
            by_user_by_bucket[user.id].setdefault(bucket.id, 0)
            by_user_by_bucket[user.id][bucket.id] += shares
            by_user[user.id] += shares
            total_shares += shares

    stats = {"buckets": bucket_info}
    members = []
    for user_id, user_total_shares in by_user.items():
        user = GooseUser.objects.get(pk=user_id)
        total_percent = round((Decimal(user_total_shares) / total_shares) * 100, 2)
        buckets = []
        for bucket_id, users_share_in_bucket in by_user_by_bucket[user_id].items():
            total_shares = total_item_shares_per_bucket[bucket_id]
            bucket_percent = percent(users_share_in_bucket, total_shares)
            buckets.append(
                {
                    "id": bucket_id,
                    "percent_owned": bucket_percent,
                    "their_shares": users_share_in_bucket,
                    "total_shares": total_shares,
                }
            )
        members.append(
            {
                "username": user.username,
                "total_percent": total_percent,
                "buckets": buckets,
            }
        )
    stats["members"] = sorted(members, key=lambda x: x["total_percent"], reverse=True)
    return stats


def percent(n, y):
    return str(round((Decimal(n) / y) * 100, 2))
