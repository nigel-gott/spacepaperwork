import json

from django.contrib import messages
from django.db import transaction
from django.db.models.query_utils import Q
from django.forms.forms import Form
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from goosetools.contracts.forms import ItemMoveAllForm
from goosetools.contracts.models import Contract
from goosetools.contracts.serializers import ContractSerializer
from goosetools.fleets.models import Fleet
from goosetools.items.models import (
    CharacterLocation,
    InventoryItem,
    ItemLocation,
    StackedInventoryItem,
)


def forbidden(request):
    messages.error(request, "You are forbidden to access this.")
    return render(request, "contracts/403.html")


def pending_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == "POST":
        form = Form(request.POST)
        if form.is_valid() and contract.can_change_status_to(
            request.gooseuser, "pending"
        ):
            change_contract_status(contract, "pending")
    return HttpResponseRedirect(reverse("view_contract", args=[pk]))


def reject_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == "POST":
        form = Form(request.POST)
        if form.is_valid() and contract.can_change_status_to(
            request.gooseuser, "rejected"
        ):
            change_contract_status(contract, "rejected")
    return HttpResponseRedirect(reverse("view_contract", args=[pk]))


@transaction.atomic
def cancel_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == "POST":
        if contract.can_change_status_to(request.gooseuser, "cancelled"):
            change_contract_status(contract, "cancelled")
        else:
            messages.error(request, "You cannot cancel someone elses contract")
        return HttpResponseRedirect(reverse("view_contract", args=[pk]))
    else:
        return render(
            request, "contracts/cancel_contract_form.html", {"contract": contract}
        )


def change_contract_status(contract, status):
    contract.change_status(status)
    char_loc, _ = CharacterLocation.objects.get_or_create(
        character=contract.to_char, system=contract.system
    )
    loc, _ = ItemLocation.objects.get_or_create(
        character_location=char_loc, corp_hanger=None
    )
    if status not in ("requested", "pending"):
        contract.save_items_to_log(clear_items=False)
        if status == "accepted":
            contract.inventoryitem_set.update(location=loc)
        contract.inventoryitem_set.update(contract=None)


@transaction.atomic
def accept_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == "POST":
        form = Form(request.POST)
        if form.is_valid() and contract.can_change_status_to(
            request.gooseuser, "accepted"
        ):
            change_contract_status(contract, "accepted")
    return HttpResponseRedirect(reverse("view_contract", args=[pk]))


@transaction.atomic
def create_contract_item_stack(request, pk):
    stack = get_object_or_404(StackedInventoryItem, pk=pk)
    if request.method == "POST":
        form = ItemMoveAllForm(request.POST)
        if form.is_valid():
            if not stack.has_admin(request.gooseuser):
                messages.error(
                    request, f"You do not have permission to move stack {stack}"
                )
                return forbidden(request)
            if stack.quantity() == 0:
                messages.error(
                    request,
                    "You cannot contract an stack which is being or has been sold",
                )
                return forbidden(request)
            system = form.cleaned_data["system"]
            character = form.cleaned_data["character"]

            contract = Contract.create(
                from_user=request.gooseuser,
                to_char=character,
                system=system,
                status="pending",
            )
            for item in stack.items():
                if item.contract:
                    messages.error(
                        request,
                        f"An item ({item}) in the stack is already in a contract, "
                        f"all items in the stack must not be in a contract before you "
                        f"can contract the entire stack. ",
                    )
                    return forbidden(request)
                item.contract = contract
                item.full_clean()
                item.save()
            return HttpResponseRedirect(reverse("contracts") + "?status_filter=sent")
    else:
        form = ItemMoveAllForm()
    return render(
        request,
        "contracts/item_move_all.html",
        {"form": form, "title": f"Contract Individual Stack: {stack}"},
    )


@transaction.atomic
def create_contract_item(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == "POST":
        form = ItemMoveAllForm(request.POST)
        if form.is_valid():
            if not item.has_admin(request.gooseuser):
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

            contract = Contract.create(
                from_user=request.gooseuser,
                to_char=character,
                system=system,
                status="pending",
            )
            item.contract = contract
            item.full_clean()
            item.save()
            return HttpResponseRedirect(reverse("contracts") + "?status_filter=sent")
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
            if not loc.has_admin(request.gooseuser):
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

            contract = Contract.create(
                from_user=request.gooseuser,
                to_char=character,
                system=system,
                status="pending",
            )
            items_in_location.update(contract=contract)
            return HttpResponseRedirect(reverse("contracts") + "?status_filter=sent")
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
            if not loc.has_admin(request.gooseuser):
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

            contract = Contract.create(
                from_user=request.gooseuser,
                to_char=character,
                system=system,
                status="pending",
            )
            items_in_location.update(contract=contract)
            return HttpResponseRedirect(reverse("contracts") + "?status_filter=sent")
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
                location__character_location__character__user=request.gooseuser,
                quantity__gt=0,
                marketorder__isnull=True,
                solditem__isnull=True,
            )
            if all_your_items.count() == 0:
                messages.error(request, "You have no items to contract :'(")
                return forbidden(request)

            contract = Contract.create(
                from_user=request.gooseuser,
                to_char=character,
                system=system,
                status="pending",
            )
            all_your_items.update(contract=contract)
            return HttpResponseRedirect(reverse("contracts") + "?status_filter=sent")
    else:
        form = ItemMoveAllForm()

    return render(
        request,
        "contracts/item_move_all.html",
        {"form": form, "title": "Contract All Your Items"},
    )


def view_contract(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if contract.status == "pending" or contract.status == "requested":
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


class ContractQuerySet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet
):
    queryset = Contract.objects.all()

    def get_queryset(self):
        return Contract.objects.filter(
            Q(from_user=self.request.gooseuser)
            | Q(to_char__user=self.request.gooseuser)
        )

    serializer_class = ContractSerializer

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def cancelled(self, request, pk=None):
        return self._change_status(request, "cancelled")

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def pending(self, request, pk=None):
        return self._change_status(request, "pending")

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def accepted(self, request, pk=None):
        return self._change_status(request, "accepted")

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def rejected(self, request, pk=None):
        return self._change_status(request, "rejected")

    def _change_status(self, request, status):
        contract = self.get_object()
        if contract.can_change_status_to(request.gooseuser, status):
            change_contract_status(contract, status)
            serializer = self.get_serializer(contract)
            return Response(serializer.data)
        else:
            return Response(
                {"error": "You are not able to change the status of that contract."}
            )


def contracts(request):
    actionable = ["pending", "requested"]
    return render(
        request,
        "contracts/contracts.html",
        {
            "my_contracts_pending": Contract.objects.filter(
                from_user=request.gooseuser, status="pending"
            ),
            "my_contracts_requested": Contract.objects.filter(
                from_user=request.gooseuser, status="requested"
            ),
            "to_me_contracts_pending": list(
                Contract.objects.filter(
                    to_char__user=request.gooseuser, status="pending"
                )
            ),
            "to_me_contracts_requested": list(
                Contract.objects.filter(
                    to_char__user=request.gooseuser, status="requested"
                )
            ),
            "old_my_contracts": Contract.objects.filter(
                from_user=request.gooseuser
            ).exclude(status__in=actionable),
            "old_to_me_contracts": Contract.objects.filter(
                to_char__user=request.gooseuser
            ).exclude(status__in=actionable),
        },
    )


def contract_dashboard(request):
    actionable_count = Contract.objects.filter(
        Q(from_user=request.gooseuser) & Q(status="requested")
        | Q(to_char__user=request.gooseuser) & Q(status="pending")
    ).count()
    mine_count = Contract.objects.filter(
        Q(to_char__user=request.gooseuser) & Q(status="requested")
        | Q(from_user=request.gooseuser) & Q(status="pending")
    ).count()
    old_count = Contract.objects.filter(
        (Q(from_user=request.gooseuser) | Q(to_char__user=request.gooseuser))
        & (Q(status="accepted") | Q(status="rejected") | Q(status="cancelled"))
    ).count()
    return render(
        request,
        "contracts/contract_dashboard.html",
        {
            "actionable_count": actionable_count,
            "mine_count": mine_count,
            "old_count": old_count,
            "page_data": {
                "gooseuser_id": request.gooseuser.id,
                "site_prefix": f"/{request.site_prefix}",
                "ajax_url": reverse("contract-list"),
                "contract_view_url": reverse("view_contract", args=[0]),
                "status_filter": request.GET.get("status_filter", ""),
            },
            "gooseuser": request.gooseuser,
        },
    )
