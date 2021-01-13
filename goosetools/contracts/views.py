import json
import math as m
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.forms.forms import Form
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone, translation
from djmoney.money import Money
from moneyed.localization import format_money

from goosetools.contracts.forms import ItemMoveAllForm
from goosetools.contracts.models import Contract
from goosetools.fleets.models import Fleet
from goosetools.items.models import CharacterLocation, InventoryItem, ItemLocation


def forbidden(request):
    messages.error(request, "You are forbidden to access this.")
    return render(request, "contracts/403.html")


def reject_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == "POST":
        form = Form(request.POST)
        if form.is_valid() and contract.can_accept_or_reject(request.user):
            contract.status = "rejected"
            log = []
            for item in contract.inventoryitem_set.all():
                log.append(
                    {
                        "id": item.id,
                        "item": str(item),
                        "quantity": item.quantity,
                        "status": item.status(),
                        "loot_group_id": item.loot_group and item.loot_group.id,
                    }
                )
            contract.log = json.dumps(log, cls=ComplexEncoder)
            contract.full_clean()
            contract.save()
            contract.inventoryitem_set.update(contract=None)
    return HttpResponseRedirect(reverse("view_contract", args=[pk]))


@transaction.atomic
def cancel_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == "POST":
        if contract.can_cancel(request.user):
            change_contract_status(contract, "cancelled", False)
        else:
            messages.error(request, "You cannot cancel someone elses contract")
        return HttpResponseRedirect(reverse("view_contract", args=[pk]))
    else:
        return render(
            request, "contracts/cancel_contract_form.html", {"contract": contract}
        )


class ComplexEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Money):
            return format_money(o, locale=translation.get_language())
        if isinstance(o, Decimal):
            return str(m.floor(o))
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, o)


def change_contract_status(contract, status, change_location):
    contract.status = status
    char_loc, _ = CharacterLocation.objects.get_or_create(
        character=contract.to_char, system=contract.system
    )
    loc, _ = ItemLocation.objects.get_or_create(
        character_location=char_loc, corp_hanger=None
    )
    log = []
    for item in contract.inventoryitem_set.all():
        log.append(
            {
                "id": item.id,
                "item": str(item),
                "quantity": item.quantity,
                "status": item.status(),
                "loot_group_id": item.loot_group and item.loot_group.id,
            }
        )
    contract.log = json.dumps(log, cls=ComplexEncoder)
    contract.full_clean()
    contract.save()
    if change_location:
        contract.inventoryitem_set.update(location=loc)
    contract.inventoryitem_set.update(contract=None)


@transaction.atomic
def accept_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == "POST":
        form = Form(request.POST)
        if form.is_valid() and contract.can_accept_or_reject(request.user):
            change_contract_status(contract, "accepted", True)
    return HttpResponseRedirect(reverse("view_contract", args=[pk]))


@transaction.atomic
def create_contract_item(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == "POST":
        form = ItemMoveAllForm(request.POST)
        if form.is_valid():
            if not item.has_admin(request.user):
                messages.error(
                    request, f"You do not have permission to move item {item}"
                )
                return forbidden(request)
            if item.quantity == 0:
                messages.error(
                    request,
                    "You cannot contract an item which is being or has been sold",
                )
                return forbidden(request)
            system = form.cleaned_data["system"]
            character = form.cleaned_data["character"]

            contract = Contract(
                from_user=request.user,
                to_char=character,
                system=system,
                created=timezone.now(),
                status="pending",
            )
            contract.full_clean()
            contract.save()
            item.contract = contract
            item.full_clean()
            item.save()
            return HttpResponseRedirect(reverse("contracts"))
    else:
        form = ItemMoveAllForm()
    return render(
        request,
        "contracts/item_move_all.html",
        {"form": form, "title": f"Contract Individual Item: {item}"},
    )


@transaction.atomic
def create_contract_for_loc(request, pk):
    loc = get_object_or_404(ItemLocation, pk=pk)
    if request.method == "POST":
        form = ItemMoveAllForm(request.POST)
        if form.is_valid():
            if not loc.has_admin(request.user):
                messages.error(
                    request, f"You do not have permission to move items from {loc}"
                )
                return forbidden(request)
            system = form.cleaned_data["system"]
            character = form.cleaned_data["character"]
            items_in_location = InventoryItem.objects.filter(
                contract__isnull=True,
                location=loc,
                quantity__gt=0,
                marketorder__isnull=True,
                solditem__isnull=True,
            )
            if items_in_location.count() == 0:
                messages.error(request, "You have no items to contract :'(")
                return forbidden(request)

            contract = Contract(
                from_user=request.user,
                to_char=character,
                system=system,
                created=timezone.now(),
                status="pending",
            )
            contract.full_clean()
            contract.save()
            items_in_location.update(contract=contract)
            return HttpResponseRedirect(reverse("contracts"))
    else:
        form = ItemMoveAllForm()
    return render(
        request,
        "contracts/item_move_all.html",
        {"form": form, "title": f"Contract All Your Items In {loc}"},
    )


@transaction.atomic
def create_contract_for_fleet(request, fleet_pk, loc_pk):
    f = get_object_or_404(Fleet, pk=fleet_pk)
    loc = get_object_or_404(ItemLocation, pk=loc_pk)
    if request.method == "POST":
        form = ItemMoveAllForm(request.POST)
        if form.is_valid():
            if not loc.has_admin(request.user):
                messages.error(
                    request, f"You do not have permission to move items from {loc}"
                )
                return forbidden(request)
            system = form.cleaned_data["system"]
            character = form.cleaned_data["character"]
            items_in_location = InventoryItem.objects.filter(
                contract__isnull=True,
                loot_group__fleet_anom__fleet=f,
                location=loc,
                quantity__gt=0,
                marketorder__isnull=True,
                solditem__isnull=True,
            )
            if items_in_location.count() == 0:
                messages.error(request, "You have no items to contract :'(")
                return forbidden(request)

            contract = Contract(
                from_user=request.user,
                to_char=character,
                system=system,
                created=timezone.now(),
                status="pending",
            )
            contract.full_clean()
            contract.save()
            items_in_location.update(contract=contract)
            return HttpResponseRedirect(reverse("contracts"))
    else:
        form = ItemMoveAllForm()
    return render(
        request,
        "contracts/item_move_all.html",
        {"form": form, "title": f"Contract Your Items From Fleet:{f} {loc}"},
    )


@transaction.atomic
def item_move_all(request):
    if request.method == "POST":
        form = ItemMoveAllForm(request.POST)
        if form.is_valid():
            system = form.cleaned_data["system"]
            character = form.cleaned_data["character"]
            all_your_items = InventoryItem.objects.filter(
                contract__isnull=True,
                location__character_location__character__user=request.user,
                quantity__gt=0,
                marketorder__isnull=True,
                solditem__isnull=True,
            )
            if all_your_items.count() == 0:
                messages.error(request, "You have no items to contract :'(")
                return forbidden(request)

            contract = Contract(
                from_user=request.user,
                to_char=character,
                system=system,
                created=timezone.now(),
                status="pending",
            )
            contract.full_clean()
            contract.save()
            all_your_items.update(contract=contract)
            return HttpResponseRedirect(reverse("contracts"))
    else:
        form = ItemMoveAllForm()

    return render(
        request,
        "contracts/item_move_all.html",
        {"form": form, "title": "Contract All Your Items"},
    )


def view_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if contract.status == "pending":
        log = []
        for item in contract.inventoryitem_set.all():
            log.append(
                {
                    "id": item.id,
                    "item": str(item),
                    "quantity": item.quantity,
                    "status": item.status(),
                    "loot_group_id": item.loot_group and item.loot_group.id,
                }
            )
    else:
        log = json.loads(contract.log)

    return render(
        request, "contracts/contract_view.html", {"contract": contract, "log": log}
    )


def contracts(request):
    return render(
        request,
        "contracts/contracts.html",
        {
            "my_contracts": Contract.objects.filter(
                from_user=request.user, status="pending"
            ),
            "to_me_contracts": list(
                Contract.objects.filter(to_char__user=request.user, status="pending")
            ),
            "old_my_contracts": Contract.objects.filter(from_user=request.user).exclude(
                status="pending"
            ),
            "old_to_me_contracts": Contract.objects.filter(
                to_char__user=request.user
            ).exclude(status="pending"),
        },
    )
