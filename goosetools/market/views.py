import math as m
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models.expressions import F
from django.forms.formsets import formset_factory
from django.http.response import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from djmoney.money import Money

from goosetools.bank.models import EggTransaction, IskTransaction
from goosetools.items.models import (
    CharacterLocation,
    InventoryItem,
    ItemLocation,
    StackedInventoryItem,
)
from goosetools.items.views import get_items_in_location
from goosetools.market.forms import (
    BulkSellItemForm,
    BulkSellItemFormHead,
    EditOrderPriceForm,
    SellItemForm,
    SoldItemForm,
)
from goosetools.market.models import MarketOrder, SoldItem, to_isk

login_url = reverse_lazy("discord_login")


def forbidden(request):
    messages.error(request, "You are forbidden to access this.")
    return render(request, "market/403.html")


@login_required(login_url=login_url)
def stack_change_price(request, pk):
    stack = get_object_or_404(StackedInventoryItem, pk=pk)

    if not stack.has_admin(request.user):
        return forbidden(request)

    if request.method == "POST":
        form = EditOrderPriceForm(request.POST)
        if form.is_valid():
            success = True
            message = "No stacks found to change? PM @thejanitor"

            for market_order in stack.marketorders().all():  # type: ignore
                new_price = form.cleaned_data["new_price"]
                broker_fee = form.cleaned_data["broker_fee"] / 100
                inner_success, message = market_order.change_price(
                    new_price, broker_fee, request.user
                )
                success = inner_success and success
                if not success:
                    break

            if success:
                messages.success(request, "Succesfully changed the price of the stack.")
                return HttpResponseRedirect(reverse("orders"))
            else:
                raise forms.ValidationError(
                    "Failed changing one a stacks market orders: " + message
                )
    else:
        form = EditOrderPriceForm()
        form.fields["new_price"].initial = stack.list_price().amount
        form.fields["broker_fee"].initial = request.user.broker_fee
    order_json = {
        "old_price": stack.list_price().amount,
        "quantity": stack.order_quantity(),
        "broker_fee": request.user.broker_fee,
    }
    return render(
        request,
        "market/stack_edit_order_price.html",
        {
            "order_json": order_json,
            "order": stack,
            "form": form,
            "title": "Change Price of An Existing Stack Market Order",
        },
    )


@login_required(login_url=login_url)
def edit_order_price(request, pk):
    market_order = get_object_or_404(MarketOrder, pk=pk)

    if not market_order.has_admin(request.user):
        return forbidden(request)

    if request.method == "POST":
        form = EditOrderPriceForm(request.POST)
        if form.is_valid():
            new_price = form.cleaned_data["new_price"]
            broker_fee = form.cleaned_data["broker_fee"] / 100
            success, message = market_order.change_price(
                new_price, broker_fee, request.user
            )
            if success:
                messages.success(request, message)
                return HttpResponseRedirect(reverse("orders"))
            else:
                messages.error(request, message)
                return HttpResponseRedirect(reverse("edit_order_price", args=[pk]))
    else:
        form = EditOrderPriceForm()
        form.fields["new_price"].initial = market_order.listed_at_price.amount
        form.fields["broker_fee"].initial = request.user.broker_fee
    order_json = {
        "old_price": market_order.listed_at_price.amount,
        "quantity": market_order.quantity,
        "broker_fee": request.user.broker_fee,
    }
    return render(
        request,
        "market/edit_order_price.html",
        {
            "order_json": order_json,
            "order": market_order,
            "form": form,
            "title": "Change Price of An Existing Market Order",
        },
    )


def estimate_price(item, hours):
    price, datapoints, price_other = item.min_of_last_x_hours(hours)
    return price, datapoints, price_other


@login_required(login_url=login_url)
@transaction.atomic
def sell_all_items(request, pk):
    loc = get_object_or_404(CharacterLocation, pk=pk)
    if not loc.has_admin(request.user) or not request.user.is_staff:
        return HttpResponseForbidden()
    items = get_items_in_location(loc)
    BulkSellItemFormSet = formset_factory(BulkSellItemForm, extra=0)  # noqa
    hours = 24 * 7
    if request.method == "POST":
        head_form = BulkSellItemFormHead(request.POST)
        if head_form.is_valid():
            cut = head_form.cleaned_data["overall_cut"]
        else:
            cut = 35
    else:
        cut = 35
    initial = []
    for stack_id, stack_data in items["stacks"].items():
        stack = stack_data["stack"]
        estimate, datapoints, other = estimate_price(stack.item(), hours)
        quantity = stack.quantity()
        if estimate is None or not estimate or estimate * quantity > 250000:
            initial.append(
                {
                    "stack": stack_id,
                    "estimate_price": estimate,
                    "listed_at_price": estimate,
                    "quality": f"{datapoints} datapoints, {to_isk(other or 0)} sell_min",
                    "quantity": quantity,
                    "item": stack.item(),
                }
            )
    for item in items["unstacked"]:
        estimate, datapoints, other = estimate_price(item.item, hours)
        quantity = item.quantity
        if estimate is None or not estimate or estimate * quantity > 250000:
            initial.append(
                {
                    "inv_item": item.id,
                    "estimate_price": estimate,
                    "listed_at_price": estimate,
                    "quality": f"{datapoints} datapoints, {to_isk(other or 0)} sell_min",
                    "quantity": quantity,
                    "item": item.item,
                }
            )
    if request.method == "POST":
        formset = BulkSellItemFormSet(request.POST, request.FILES, initial=initial)
        head_form = BulkSellItemFormHead(request.POST)
        if formset.is_valid() and head_form.is_valid():
            for form in formset:
                inv_item = form.cleaned_data["inv_item"]
                stack = form.cleaned_data["stack"]
                cut = 1 - Decimal(head_form.cleaned_data["overall_cut"] / 100)
                uncommaed_price = form.cleaned_data["listed_at_price"].replace(",", "")
                price = Decimal(uncommaed_price)
                cut_price = price * cut
                items = []
                if inv_item:
                    items = [inv_item]
                else:
                    items = stack.inventoryitem_set.all()
                for item in items:
                    if not item.can_sell():
                        messages.error(
                            request,
                            f"Item {item} cannot be sold, maybe it is already being sold or is in a pending contract?",
                        )
                        return HttpResponseRedirect(reverse("sell_all", args=[pk]))
                    profit_line = IskTransaction(
                        item=item,
                        time=timezone.now(),
                        isk=to_isk(m.floor(cut_price * item.quantity)),
                        quantity=item.quantity,
                        transaction_type="buyback",
                        notes=f"Corp Buyback using price {price} and a cut for the corp of {cut * 100}% ",
                    )
                    profit_line.full_clean()
                    profit_line.save()
                    sold_item = SoldItem(
                        item=item, quantity=item.quantity, sold_via="internal"
                    )
                    sold_item.full_clean()
                    sold_item.save()
                    item.quantity = 0
                    item.full_clean()
                    item.save()

            messages.success(request, "Items succesfully bought")
            return HttpResponseRedirect(reverse("sold"))
        else:
            messages.error(request, f"Invalid {formset.errors} {head_form.errors}")
    else:
        head_form = BulkSellItemFormHead()
        formset = BulkSellItemFormSet(initial=initial)
    return render(
        request,
        "market/sell_all.html",
        {
            "formset": formset,
            "head_form": head_form,
            "title": "Change Price of An Existing Market Order",
        },
    )


@login_required(login_url=login_url)
def sold(request):
    characters = request.user.characters()
    all_sold = []
    for char in characters:
        char_locs = CharacterLocation.objects.filter(character=char)
        for char_loc in char_locs:
            loc = ItemLocation.objects.get(
                character_location=char_loc, corp_hanger=None
            )
            untransfered_sold_items = SoldItem.objects.filter(
                item__location=loc, quantity__gt=F("transfered_quantity")
            )
            all_sold.append({"loc": loc, "sold": untransfered_sold_items})

    return render(
        request,
        "market/sold.html",
        {
            "transfer_logs": request.user.transferlog_set.filter(all_done=False)
            .order_by("-time")
            .all(),
            "all_sold": all_sold,
        },
    )


@login_required(login_url=login_url)
def orders(request):
    characters = request.user.characters()
    all_orders = []
    for char in characters:
        char_locs = CharacterLocation.objects.filter(character=char)
        for char_loc in char_locs:
            market_items = InventoryItem.objects.filter(marketorder__isnull=False)
            items = get_items_in_location(char_loc, market_items)
            if items["total_in_loc"] > 0:
                all_orders.append(items)

    return render(request, "market/orders.html", {"all_orders": all_orders})


def item_sold(order, remaining_quantity_to_sell):
    transaction_tax_percent = order.transaction_tax / 100
    quantity_sold = min(order.quantity, remaining_quantity_to_sell)
    quantity_remaining = order.quantity - quantity_sold
    gross_profit = order.listed_at_price * quantity_sold
    transaction_tax = Money(
        amount=m.floor((gross_profit * transaction_tax_percent).amount), currency="EEI"
    )
    item = order.item
    transaction_tax_line = IskTransaction(
        item=item,
        time=timezone.now(),
        isk=-transaction_tax,
        quantity=quantity_sold,
        transaction_type="transaction_tax",
        notes=f" - Gross Profit of {gross_profit} * Tax of {transaction_tax_percent * 100}%",
    )
    transaction_tax_line.full_clean()
    transaction_tax_line.save()
    profit_line = IskTransaction(
        item=item,
        time=timezone.now(),
        isk=to_isk(m.floor(gross_profit.amount)),
        quantity=quantity_sold,
        transaction_type="external_market_gross_profit",
        notes=f"Order Price of {order.listed_at_price} * Quantity Sold of {quantity_sold}",
    )
    profit_line.full_clean()
    profit_line.save()
    sold_item, sold_item_created = SoldItem.objects.get_or_create(
        item=item, defaults={"quantity": quantity_sold, "sold_via": "external"}
    )
    if not sold_item_created:
        sold_item.quantity = sold_item.quantity + quantity_sold
        sold_item.full_clean()
        sold_item.save()

    if quantity_remaining == 0:
        order.delete()
    else:
        order.quantity = quantity_remaining
        order.full_clean()
        order.save()
    return remaining_quantity_to_sell - quantity_sold


@login_required(login_url=login_url)
@transaction.atomic
def stack_sold(request, pk):
    stack = get_object_or_404(StackedInventoryItem, pk=pk)
    if not stack.has_admin(request.user):
        return forbidden(request)

    if request.method == "POST":
        form = SoldItemForm(request.POST)
        if form.is_valid():
            quantity_remaining = form.cleaned_data["quantity_remaining"]
            total_to_sell = stack.order_quantity() - quantity_remaining
            saved_total = total_to_sell
            if total_to_sell <= 0:
                messages.error(
                    request, "You requested to sell 0 of this stack which is silly"
                )
            else:
                for market_order in stack.marketorders():  # type: ignore
                    if total_to_sell <= 0:
                        break
                    total_to_sell = item_sold(market_order, total_to_sell)
                messages.success(request, f"Sold {saved_total} of the stack!")
            return HttpResponseRedirect(reverse("orders"))
    else:
        form = SoldItemForm(initial={"quantity_remaining": 0})
    return render(
        request,
        "market/order_sold.html",
        {"form": form, "title": "Mark Stack As Sold", "order": stack},
    )


@login_required(login_url=login_url)
@transaction.atomic
def order_sold(request, pk):
    order = get_object_or_404(MarketOrder, pk=pk)
    if not order.has_admin(request.user):
        return forbidden(request)

    if request.method == "POST":
        form = SoldItemForm(request.POST)
        if form.is_valid():
            quantity_remaining = form.cleaned_data["quantity_remaining"]
            quantity_to_sell = order.quantity - quantity_remaining
            if quantity_to_sell <= 0:
                messages.error(request, "Cannot sell 0 or fewer items")
            else:
                item_sold(order, quantity_to_sell)
                messages.success(
                    request, f"Sold {quantity_to_sell} of item {order.item}"
                )
            return HttpResponseRedirect(reverse("orders"))
    else:
        form = SoldItemForm(initial={"quantity_remaining": 0})
    return render(
        request,
        "market/order_sold.html",
        {
            "form": form,
            "title": "Mark Order As Sold",
            "order": order,
            "url_to_order": reverse("item_view", args=[order.item.id]),
        },
    )


def split_off(item, new_quantity, new_stack=None):
    if item.junked_quantity() + item.order_quantity() + item.sold_quantity() > 0:
        raise Exception("Cannot split and item that has been junked, sold or listed.")
    new_item = InventoryItem.objects.create(
        item=item.item,
        quantity=new_quantity,
        created_at=item.created_at,
        location=item.location,
        loot_group=item.loot_group,
        contract=item.contract,
        stack=new_stack,
    )
    updated_quantity = item.quantity - new_quantity
    for isk_tran in item.isktransaction_set.all():
        isk_tran.isk = (isk_tran.isk / item.quantity) * updated_quantity
        isk_tran.quantity = updated_quantity
        isk_tran.save()
        IskTransaction.objects.create(
            item=new_item,
            transaction_type=isk_tran.transaction_type,
            notes=isk_tran.notes,
            time=isk_tran.time,
        )
    for egg_tran in item.eggtransaction_set.all():
        egg_tran.eggs = (egg_tran.isk / item.quantity) * updated_quantity
        egg_tran.quantity = updated_quantity
        egg_tran.save()
        EggTransaction.objects.create(
            item=new_item,
            notes=egg_tran.notes,
            time=egg_tran.time,
            debt=egg_tran.debt,
            counterparty_discord_username=egg_tran.counterparty_discord_username,
        )
    item.quantity = updated_quantity
    item.full_clean()
    item.save()
    return new_item


def sell_item(item, form, quantity_to_sell, new_stack=None):
    if item.quantity > quantity_to_sell:
        item = item.split_off(quantity_to_sell, new_stack)
    remaining_quantity_to_sell = quantity_to_sell - item.quantity
    price = Decimal(form.cleaned_data["listed_at_price"].replace(",", ""))
    total_isk_listed = item.quantity * price
    broker_fee_percent = form.cleaned_data["broker_fee"] / 100
    broker_fee = Money(
        amount=m.floor(-(total_isk_listed * broker_fee_percent)), currency="EEI"
    )
    broker_fee = IskTransaction(
        item=item,
        time=timezone.now(),
        isk=broker_fee,
        quantity=item.quantity,
        transaction_type="broker_fee",
        notes=f"- Quantity of {item.quantity} * Listed Price at {price} * Broker Fee of {broker_fee_percent * 100}%",
    )
    broker_fee.full_clean()
    broker_fee.save()
    sell_order = MarketOrder(
        item=item,
        internal_or_external="external",
        buy_or_sell="sell",
        quantity=item.quantity,
        listed_at_price=price,
        transaction_tax=form.cleaned_data["transaction_tax"],
        broker_fee=form.cleaned_data["broker_fee"],
    )
    sell_order.full_clean()
    sell_order.save()
    item.quantity = 0
    item.stack = new_stack
    item.save()
    return remaining_quantity_to_sell


@login_required(login_url=login_url)
@transaction.atomic
def stack_sell(request, pk):
    stack = get_object_or_404(StackedInventoryItem, pk=pk)
    if not stack.has_admin(request.user):
        messages.error(request, f"You do not have permission to sell stack {stack.id}")
        return HttpResponseRedirect(reverse("items"))

    if not stack.can_sell():
        messages.error(
            request,
            f"You cannot sell {stack} as it is already being sold, has been contracted, or has been sold already.",
        )
        return HttpResponseRedirect(reverse("items"))

    if request.method == "POST":
        form = SellItemForm(stack.quantity(), request.POST)
        if form.is_valid():
            quantity_to_sell = form.cleaned_data["quantity"]
            if quantity_to_sell < stack.quantity():
                new_stack = StackedInventoryItem.objects.create(
                    created_at=stack.created_at
                )
            else:
                new_stack = stack
            for item in stack.items():
                if quantity_to_sell > 0:
                    quantity_to_sell = sell_item(
                        item, form, quantity_to_sell, new_stack
                    )
                else:
                    break
            messages.success(request, "Succesfully created market order for stack")
            return HttpResponseRedirect(reverse("items"))
    else:
        form = SellItemForm(
            stack.quantity(),
            initial={
                "quantity": stack.quantity(),
                "broker_fee": request.user.broker_fee,
                "transaction_tax": request.user.transaction_tax,
            },
        )

    order_json = {"quantity": stack.quantity()}

    return render(
        request,
        "market/sell_stack.html",
        {
            "form": form,
            "title": f"Sell Stack {stack}",
            "stack": stack,
            "order_json": order_json,
        },
    )


@login_required(login_url=login_url)
@transaction.atomic
def item_sell(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if not item.has_admin(request.user):
        return forbidden(request)

    if item.quantity == 0:
        messages.error(request, "Cannot sell an item with 0 quantity.")
        return forbidden(request)

    if request.method == "POST":
        form = SellItemForm(item.quantity, request.POST)
        if form.is_valid():
            form_quantity = form.cleaned_data["quantity"]
            sell_item(item, form, form_quantity)
            return HttpResponseRedirect(reverse("items"))
    else:
        form = SellItemForm(
            item.quantity,
            initial={
                "quantity": item.quantity,
                "broker_fee": request.user.broker_fee,
                "transaction_tax": request.user.transaction_tax,
            },
        )

    order_json = {"quantity": item.quantity}

    return render(
        request,
        "market/sell_stack.html",
        {"form": form, "title": "Sell Item", "item": item, "order_json": order_json},
    )