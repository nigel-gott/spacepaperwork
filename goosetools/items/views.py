import csv
import math
from typing import Any, Dict, List

from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool, NumeralTickFormatter
from bokeh.plotting import figure
from django import forms
from django.contrib import messages
from django.db import transaction
from django.db.models import ExpressionWrapper, F, Sum
from django.db.models.fields import FloatField
from django.db.models.functions import Coalesce
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView
from django_pandas.io import read_frame

from goosetools.items.forms import (
    DeleteItemForm,
    InventoryItemForm,
    ItemChangeProposalForm,
    ItemChangeProposalSelectForm,
    JunkItemsForm,
)
from goosetools.items.models import (
    CharacterLocation,
    InventoryItem,
    Item,
    ItemChangeError,
    ItemChangeProposal,
    ItemLocation,
    JunkedItem,
    StackedInventoryItem,
    to_isk,
)
from goosetools.notifications.notification_types import NOTIFICATION_TYPES
from goosetools.users.forms import CharacterForm
from goosetools.users.models import Character


def forbidden(request):
    messages.error(request, "You are forbidden to access this.")
    return render(request, "items/403.html")


def junk(request):
    characters = request.gooseuser.characters()
    all_junked = []
    for char in characters:
        char_locs = CharacterLocation.objects.filter(character=char)
        for char_loc in char_locs:
            loc = ItemLocation.objects.get(
                character_location=char_loc, corp_hanger=None
            )
            sum_query = ExpressionWrapper(
                Coalesce(F("item__item__cached_lowest_sell"), 0) * F("quantity"),
                output_field=FloatField(),
            )
            junked = (
                JunkedItem.objects.filter(item__location=loc)
                .annotate(estimated_profit_sum=sum_query)
                .order_by("-estimated_profit_sum")
            )

            all_junked.append({"loc": loc, "junked": junked})

    return render(request, "items/junk.html", {"all_junked": all_junked})


def items_view(request):
    characters = request.gooseuser.characters()
    return render_item_view(
        request,
        characters,
        True,
        "Your Items Waiting To Be Sold Or Contracted to a Seller",
    )


def items_grouped(request):
    items = (
        Item.objects.annotate(total=Sum("inventoryitem__quantity"))
        .filter(total__gt=0)
        .order_by("item_type")
    )
    return render(
        request,
        "items/grouped_items.html",
        {"items": items, "title": "All Not Sold Items In Goosetools Grouped Together"},
    )


def all_items(request):
    characters = Character.objects.annotate(
        cc=Sum("characterlocation__itemlocation__inventoryitem__quantity")
    ).filter(cc__gt=0)
    result = render_item_view(request, characters, False, "All Items")
    return result


def all_items_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="item_dump.csv"'

    writer = csv.writer(response)
    writer.writerow(['"Item Name"', '"Created At"', "Quantity", '"Item Type"'])
    total = InventoryItem.objects.count()
    print("Processing " + str(total) + " Items ")
    i = 0
    for item in InventoryItem.objects.select_related(
        "marketorder", "junkeditem", "solditem", "item"
    ).all():
        i = i + 1
        if i % math.floor(total / 100) == 0:
            print(f"{i}/{total}")

        writer.writerow(
            [
                item.item.name,
                item.created_at,
                item.total_quantity(),
                item.item.item_type,
            ]
        )

    return response


def get_items_in_location(char_loc, item_source=None):
    loc = ItemLocation.objects.get(character_location=char_loc, corp_hanger=None)
    if item_source is None:
        item_source = InventoryItem.objects.filter(quantity__gt=0)
    unstacked_items = (
        item_source.filter(stack__isnull=True, contract__isnull=True, location=loc)
        .annotate(
            estimated_profit_sum=ExpressionWrapper(
                Coalesce(F("item__cached_lowest_sell"), 0)
                * (F("quantity") + Coalesce(F("marketorder__quantity"), 0)),
                output_field=FloatField(),
            )
        )
        .order_by("-estimated_profit_sum")
    )
    stacked_items = item_source.filter(
        stack__isnull=False, contract__isnull=True, location=loc
    ).order_by("-item__cached_lowest_sell")
    stacks = {}
    stacks_by_item: Dict[int, List[Any]] = {}
    for item in stacked_items.all():
        if item.stack.id not in stacks:
            stacks[item.stack.id] = {
                "type": "stack",
                "stack": item.stack,
                "stack_id": item.stack.id,
                "item": item.item,
                "quantity": item.quantity,
            }
            if item.item.name not in stacks_by_item:
                stacks_by_item[item.item.name] = []
            stacks_by_item[item.item.name].append(stacks[item.stack.id])
        else:
            stack = stacks[item.stack.id]
            if item.item != stack["item"]:
                raise forms.ValidationError("Invalid Stack Found: " + item.stack.id)
            stack["quantity"] = stack["quantity"] + item.quantity
    total_in_loc = len(unstacked_items) + len(stacked_items.values("stack").distinct())

    return {
        "total_in_loc": total_in_loc,
        "loc": char_loc,
        "char": char_loc.character,
        "unstacked": unstacked_items,
        "stacks": {
            k: stacks[k]
            for k in sorted(
                stacks,
                key=lambda x: stacks[x]["stack"].estimated_profit() or to_isk(0),
                reverse=True,
            )
        },
        "stacks_by_item": stacks_by_item,
    }


def render_item_view(request, characters, show_contract_all, title):
    all_items_for_characters = []
    for char in characters:
        char_locs = CharacterLocation.objects.filter(character=char)
        for char_loc in char_locs:
            items = get_items_in_location(char_loc)
            if items["total_in_loc"] > 0:
                all_items_for_characters.append(items)
    result = render(
        request,
        "items/items.html",
        {
            "all_items": all_items_for_characters,
            "show_contract_all": show_contract_all,
            "title": title,
        },
    )
    return result


def stack_in_location(loc):
    items = get_items_in_location(loc)
    unstacked = items["unstacked"]
    stacks_by_item = items["stacks_by_item"]
    merged_stacks_by_item = {}
    for item, stacks in stacks_by_item.items():
        merge_stack = stacks[0]
        for stack in stacks[1:]:
            InventoryItem.objects.filter(stack=stack["stack_id"]).update(
                stack=merge_stack["stack_id"]
            )
            StackedInventoryItem.objects.get(id=stack["stack_id"]).delete()
        merged_stacks_by_item[item] = merge_stack["stack_id"]

    for unstacked_item in unstacked.all():
        item_name = unstacked_item.item.name
        if item_name not in merged_stacks_by_item:
            new_stack = StackedInventoryItem(created_at=timezone.now())
            new_stack.full_clean()
            new_stack.save()
            merged_stacks_by_item[item_name] = new_stack.id
        unstacked_item.stack_id = merged_stacks_by_item[item_name]
        unstacked_item.full_clean()
        unstacked_item.save()
    return True, f"Stacked All Items in {loc}!"


@transaction.atomic
def stack_view(request, pk):
    stack = get_object_or_404(StackedInventoryItem, pk=pk)
    return render(
        request,
        "items/view_item_stack.html",
        {
            "items": stack.inventoryitem_set.all(),
            "title": f"Viewing Item Stack {pk} in {stack.loc()}",
        },
    )


@transaction.atomic
def stack_delete(request, pk):
    stack = get_object_or_404(StackedInventoryItem, pk=pk)
    if request.method == "POST":
        if not stack.has_admin(request.gooseuser):
            messages.error(
                request, f"You do not have permission to delete stack {stack.id}"
            )
            return HttpResponseRedirect(reverse("items"))
        InventoryItem.objects.filter(stack=stack.id).update(stack=None)
        messages.success(request, f"Deleted stack {stack.id}")
        return HttpResponseRedirect(reverse("items"))

    return render(
        request,
        "items/delete_item_stack_confirm.html",
        {"items": stack.inventoryitem_set.all()},
    )


@transaction.atomic
def unjunk_item(request, pk):
    junked_item = get_object_or_404(JunkedItem, pk=pk)
    if not junked_item.item.has_admin(request.gooseuser):
        messages.error(request, "You do not have permission to unjunk this item.")
        return HttpResponseRedirect(reverse("items"))
    if request.method == "POST":
        if junked_item.item.stack:
            junked_item.item.stack.unjunk()
        else:
            junked_item.unjunk()
        return HttpResponseRedirect(reverse("junk"))
    else:
        return render(
            request,
            "items/junk_single.html",
            {"title": f"Unjunk Item {junked_item}"},
        )


@transaction.atomic
def junk_stack(request, pk):
    stack = get_object_or_404(StackedInventoryItem, pk=pk)
    if not stack.has_admin(request.gooseuser):
        messages.error(request, "You do not have permission to junk this item.")
        return HttpResponseRedirect(reverse("items"))
    if request.method == "POST":
        if stack.can_edit():
            stack.junk()
        else:
            messages.error(
                request, "Cannot junk this stack as it is in a contract or already sold"
            )
        return HttpResponseRedirect(reverse("items"))
    else:
        return render(
            request,
            "items/junk_single.html",
            {"title": f"Junk Stack {stack}"},
        )


@transaction.atomic
def junk_item(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if not item.has_admin(request.gooseuser):
        messages.error(request, "You do not have permission to junk this item.")
        return HttpResponseRedirect(reverse("items"))
    if request.method == "POST":
        if item.can_edit():
            item.junk()
        else:
            messages.error(
                request, "Cannot junk this item as it is in a contract or already sold"
            )
        return HttpResponseRedirect(reverse("items"))
    else:
        return render(
            request,
            "items/junk_single.html",
            {"title": f"Junk Item {item}"},
        )


@transaction.atomic
def junk_items(request, pk):
    loc = get_object_or_404(ItemLocation, pk=pk)
    if not loc.has_admin(request.gooseuser):
        messages.error(request, "You do not have permission to junk items here.")
        return HttpResponseRedirect(reverse("items"))
    items = get_items_in_location(
        loc.character_location,
        InventoryItem.objects.filter(
            quantity__gt=0,
            contract__isnull=True,
            location=loc,
            item__cached_lowest_sell__isnull=False,
        ),
    )
    if request.method == "POST":
        form = JunkItemsForm(request.POST)
        if form.is_valid():
            count = 0
            isk = 0
            for _, stack_data in items["stacks"].items():
                stack = stack_data["stack"]
                profit = stack.estimated_profit().amount
                if profit <= form.cleaned_data["max_price"]:
                    count = count + 1
                    isk = isk + profit
                    stack.junk()
            for item in items["unstacked"]:
                profit = item.estimated_profit().amount
                if item.can_edit() and profit <= form.cleaned_data["max_price"]:
                    count = count + 1
                    isk = isk + profit
                    item.junk()
            messages.success(
                request,
                f"Succesfully junked {count} items with a total isk estimated value of {to_isk(isk)}",
            )
        return HttpResponseRedirect(reverse("junk"))
    else:
        form = JunkItemsForm(initial={"max_price": 1000000})
    return render(
        request,
        "items/junk_item_form.html",
        {"form": form, "items": items, "title": f"Junk Cheap Items In {loc}"},
    )


@transaction.atomic
def stack_items(request, pk):
    loc = get_object_or_404(ItemLocation, pk=pk)
    items_in_location = get_items_in_location(loc.character_location)
    if request.method == "POST":
        if not loc.has_admin(request.gooseuser):
            messages.error(
                request, f"You do not have permission to stack items in {loc}"
            )
            return HttpResponseRedirect(reverse("items"))
        success, message = stack_in_location(loc.character_location)
        if success:
            messages.success(request, message)
            return HttpResponseRedirect(reverse("items"))
        else:
            messages.error(request, message)
            return HttpResponseRedirect(reverse("stack_items", args=[pk]))

    return render(
        request, "items/item_stack_confirm.html", {"items": items_in_location}
    )


def item_view(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    return render(request, "items/item_view.html", {"item": item})


def item_minus(request, pk):
    inventory_item = get_object_or_404(InventoryItem, pk=pk)
    if not inventory_item.has_admin(request.gooseuser):
        return forbidden(request)
    if request.method == "POST":
        result = inventory_item.add(-1)
        if not result:
            messages.error(
                request,
                "Failed to decrement item, maybe it's in a pending contract or being sold?",
            )
    if not inventory_item.loot_group:
        raise Exception("Missing Loot Group")
    return HttpResponseRedirect(
        reverse("loot_group_view", args=[inventory_item.loot_group.id])
    )


def item_plus(request, pk):
    inventory_item = get_object_or_404(InventoryItem, pk=pk)
    if not inventory_item.has_admin(request.gooseuser):
        return forbidden(request)
    if request.method == "POST":
        result = inventory_item.add(1)
        if not result:
            messages.error(
                request,
                "Failed to increment item, maybe it's in a pending contract or being sold?",
            )
    if not inventory_item.loot_group:
        raise Exception("Missing Loot Group")
    return HttpResponseRedirect(
        reverse("loot_group_view", args=[inventory_item.loot_group.id])
    )


def item_edit(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if not item.has_admin(request.gooseuser):
        return forbidden(request)
    if not item.can_edit():
        messages.error(
            request,
            "Cannot edit an item once market orders have been made for it. PM @thejanitor on discord to make admin edits for you.",
        )
        return forbidden(request)
    if request.method == "POST":
        form = InventoryItemForm(request.POST)
        char_form = CharacterForm(request.POST)
        if form.is_valid() and char_form.is_valid():
            char_loc = CharacterLocation.objects.get_or_create(
                character=char_form.cleaned_data["character"], system=None
            )[0]
            loc = ItemLocation.objects.get_or_create(
                character_location=char_loc, corp_hanger=None
            )

            item.location = loc[0]
            item.item = form.cleaned_data["item"]
            item.quantity = form.cleaned_data["quantity"]
            item.full_clean()
            item.save()
            if not item.loot_group:
                raise Exception("Missing Loot Group")
            return HttpResponseRedirect(
                reverse("loot_group_view", args=[item.loot_group.pk])
            )
    else:
        form = InventoryItemForm(initial={"item": item.item, "quantity": item.quantity})
        char_form = CharacterForm(
            initial={"character": request.gooseuser.default_character}
        )
        char_form.fields["character"].queryset = request.gooseuser.characters()
        char_form.fields["character"].initial = request.gooseuser.default_character
    return render(
        request,
        "items/item_edit_form.html",
        {"char_form": char_form, "form": form, "title": "Edit Item"},
    )


def item_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if not item.has_admin(request.gooseuser):
        return forbidden(request)
    if not item.can_edit():
        messages.error(
            request,
            "Cannot delete an item once market orders have been made for it. "
            "PM @thejanitor on discord to make admin edits for you.",
        )
        return forbidden(request)
    if request.method == "POST":
        form = DeleteItemForm(request.POST)
        if form.is_valid():
            if form.cleaned_data["are_you_sure"]:
                group_pk = item.loot_group and item.loot_group.pk
                item.delete()
                if group_pk:
                    return HttpResponseRedirect(
                        reverse("loot_group_view", args=[group_pk])
                    )
                else:
                    return HttpResponseRedirect(reverse("items"))
            else:
                messages.error(request, "Don't delete the item if you are not sure!")
                return HttpResponseRedirect(reverse("item_view", args=[item.pk]))

    else:
        form = DeleteItemForm()

    return render(
        request,
        "items/item_delete.html",
        {"form": form, "title": "Delete Item", "item": item},
    )


def item_db(request):
    return render(
        request,
        "items/item_db.html",
        {
            "page_data": {
                "gooseuser_id": request.gooseuser.id,
                "site_prefix": f"/{request.site_prefix}",
                "ajax_url": reverse("item-list"),
                "data_url": reverse("item_data", args=[0]),
                "propose_url": reverse("item-change-create-for-item", args=[0]),
            },
            "gooseuser": request.gooseuser,
        },
    )


class DataForm(forms.Form):
    days = forms.IntegerField(initial=7)
    style = forms.ChoiceField(
        choices=[("lines", "Lines"), ("bar", "Bar Chart"), ("scatter", "Scatter")],
        initial="lines",
    )
    show_buy_sell = forms.BooleanField(
        initial=False,
        required=False,
    )


def item_data(request, pk):
    item = get_object_or_404(Item, pk=pk)
    days = 14
    style = "lines"
    show_buy_sell = False
    if request.GET:
        form = DataForm(request.GET)
        if form.is_valid():
            days = form.cleaned_data["days"]
            style = form.cleaned_data["style"]
            show_buy_sell = form.cleaned_data["show_buy_sell"]
    else:
        form = DataForm()

    df = get_df(days, item)
    div, script = render_graph(days, df, item, show_buy_sell, style)

    result = render(
        request,
        "items/item_data.html",
        {
            "item": item,
            "script": script,
            "div": div,
            "form": form,
        },
    )
    return result


def get_df(days, item):
    time_threshold = timezone.now() - timezone.timedelta(hours=int(days) * 24)
    events_last_week = (
        item.itemmarketdataevent_set.filter(time__gte=time_threshold)
        .values("time", "sell", "buy", "highest_buy", "lowest_sell")
        .distinct()
        .all()
    )
    df = read_frame(
        events_last_week,
        fieldnames=["time", "sell", "buy", "highest_buy", "lowest_sell"],
    )
    return df


def render_graph(days, df, item, show_buy_sell, style):
    tools = "pan, wheel_zoom, box_zoom, reset, save"
    title = f"Last {days} days of market data for {item}"
    source = ColumnDataSource(df)
    p = figure(
        x_axis_type="datetime",
        tools=tools,
        plot_width=700,
        plot_height=500,
        title=title,
    )
    tooltips = [
        ("time", "$x{%F %R}"),
        (
            "highest_buy",
            "@highest_buy{0,0 $}",
        ),  # use @{ } for field names with spaces
        (
            "lowest_sell",
            "@lowest_sell{0,0 $}",
        ),  # use @{ } for field names with spaces
    ]
    if show_buy_sell:
        tooltips.append(("sell", "@sell{0,0 $}"))
        tooltips.append(("buy", "@buy{0,0 $}"))
    h = HoverTool(
        tooltips=tooltips,
        formatters={
            "$x": "datetime",  # use 'datetime' formatter for '@date' field
            "@lowest_sell": "numeral",
            # use 'printf' formatter for '@{adj close}' field
            "@highest_buy": "numeral",
            # use 'printf' formatter for '@{adj close}' field
            "@sell": "numeral",  # use 'printf' formatter for '@{adj close}' field
            "@buy": "numeral",  # use 'printf' formatter for '@{adj close}' field
            # use default 'numeral' formatter for other fields
        },
        mode="mouse",
    )
    p.add_tools(h)
    p.xaxis.major_label_orientation = math.pi / 4
    p.grid.grid_line_alpha = 0.3
    if style == "bar":
        p.vbar(
            "time",
            60 * 60 * 2 * 1000,
            "highest_buy",
            "lowest_sell",
            fill_color="#D5E1DD",
            line_color="black",
            source=source,
        )
        if show_buy_sell:
            p.segment(
                "time",
                "sell",
                "time",
                "buy",
                color="black",
                source=source,
            )
    elif style == "lines":
        p.line(
            "time",
            "highest_buy",
            legend_label="Highest Buy",
            line_width=2,
            color="green",
            source=source,
        )
        p.line(
            "time",
            "lowest_sell",
            legend_label="Lowest Sell",
            line_width=2,
            color="blue",
            source=source,
        )
        if show_buy_sell:
            p.line(
                "time",
                "buy",
                legend_label="Buy",
                line_width=2,
                color="purple",
                source=source,
            )
            p.line(
                "time",
                "sell",
                legend_label="Sell",
                line_width=2,
                color="brown",
                source=source,
            )
    else:
        if show_buy_sell:
            p.circle(
                "time",
                "sell",
                size=5,
                color="purple",
                alpha=0.5,
                legend_label="Sell",
                source=source,
            )
            p.square(
                "time",
                "buy",
                size=5,
                color="brown",
                alpha=0.5,
                legend_label="Buy",
                source=source,
            )
        p.circle(
            "time",
            "lowest_sell",
            size=3,
            color="navy",
            alpha=0.5,
            legend_label="Lowest Sell",
            source=source,
        )
        p.square(
            "time",
            "highest_buy",
            size=3,
            color="green",
            alpha=0.5,
            legend_label="Highest Buy",
            source=source,
        )
    p.yaxis[0].formatter = NumeralTickFormatter(format="0,0 $")
    script, div = components(p)
    return div, script


class ItemChangeProposalList(ListView):
    queryset = ItemChangeProposal.open_proposals()
    context_object_name = "change_list"
    template_name = "items/item_change/item_change_list.html"


def create_item_change_for_item(request, pk):
    return create_item_form(request, get_object_or_404(Item, pk=pk))


def create_item_form(request, existing_item):
    if request.method == "POST":
        form = ItemChangeProposalForm(request.POST, existing_item=existing_item)
        if form.is_valid():
            proposal = ItemChangeProposal()
            save_proposal(existing_item, form, proposal, request)
            NOTIFICATION_TYPES["itemchanges"].send()
            messages.success(request, f"Successfully created {proposal}")
            return HttpResponseRedirect(reverse("item-change-list"))
    else:
        initial = {}
        if existing_item:
            initial = {
                "name": existing_item.name,
                "item_type": existing_item.item_type,
                "eve_echoes_market_id": existing_item.eve_echoes_market_id,
            }
        form = ItemChangeProposalForm(initial=initial, existing_item=existing_item)
    return render(
        request,
        "items/item_change/item_change_form.html",
        {"form": form, "existing_item": existing_item},
    )


def select_create_item_change(request):
    if request.method == "POST":
        form = ItemChangeProposalSelectForm(request.POST)
        if form.is_valid():
            existing_item = form.cleaned_data["existing_item"]
            if existing_item:
                return HttpResponseRedirect(
                    reverse("item-change-create-for-item", args=[existing_item.pk])
                )
            else:
                return HttpResponseRedirect(reverse("item-change-create-new"))
    else:
        form = ItemChangeProposalSelectForm()
    return render(
        request,
        "items/item_change/item_change_select.html",
        {"form": form},
    )


def create_item_change(request):
    return create_item_form(request, None)


def update_item_change(request, pk):
    proposal = get_object_or_404(ItemChangeProposal, pk=pk)
    if not proposal.has_edit_admin(request.gooseuser):
        return forbidden(request)
    existing_item = proposal.existing_item
    if request.method == "POST":
        form = ItemChangeProposalForm(request.POST, existing_item=existing_item)
        if form.is_valid():
            save_proposal(existing_item, form, proposal, request)
            return HttpResponseRedirect(reverse("item-change-list"))
    else:
        initial = {"change": proposal.change}
        if existing_item:
            initial = {
                "change": proposal.change,
                "name": existing_item.name,
                "item_type": existing_item.item_type,
                "eve_echoes_market_id": existing_item.eve_echoes_market_id,
            }
        if proposal.name:
            initial["name"] = proposal.name

        if proposal.item_type:
            initial["item_type"] = proposal.item_type

        if proposal.eve_echoes_market_id:
            initial["eve_echoes_market_id"] = proposal.eve_echoes_market_id
        form = ItemChangeProposalForm(
            initial=initial,
            existing_item=existing_item,
        )

    return render(
        request,
        "items/item_change/item_change_form.html",
        {"form": form, "itemchangeproposal": proposal},
    )


def save_proposal(existing_item, form, proposal, request):
    proposal.proposed_by = request.gooseuser
    proposal.proposed_at = timezone.now()
    proposal.change = form.cleaned_data["change"]
    proposal.existing_item = existing_item
    if existing_item and existing_item.name == form.cleaned_data["name"]:
        proposal.name = None
    else:
        proposal.name = form.cleaned_data["name"]
    if existing_item and existing_item.item_type == form.cleaned_data["item_type"]:
        proposal.item_type = None
    else:
        proposal.item_type = form.cleaned_data["item_type"]
    proposal.eve_echoes_market_id = form.cleaned_data["eve_echoes_market_id"]
    if (
        existing_item
        and existing_item.eve_echoes_market_id
        == form.cleaned_data["eve_echoes_market_id"]
    ):
        proposal.eve_echoes_market_id = None
    else:
        proposal.eve_echoes_market_id = form.cleaned_data["eve_echoes_market_id"]
    proposal.save()


def approve_item_change(request, pk):
    proposal = get_object_or_404(ItemChangeProposal, pk=pk)
    if not proposal.has_approve_admin(request.gooseuser):
        return forbidden(request)

    if request.method == "POST":
        try:
            proposal.approve(request)
            if ItemChangeProposal.open_proposals().count() == 0:
                NOTIFICATION_TYPES["itemchanges"].dismiss()
            messages.success(request, f"Succesfully approved {proposal}")
        except ItemChangeError as e:
            messages.error(request, e.message)
        return HttpResponseRedirect(reverse("item-change-list"))
    else:
        return render(
            request,
            "items/item_change/item_change_approve.html",
            {"itemchangeproposal": proposal},
        )


def delete_item_change(request, pk):
    proposal = get_object_or_404(ItemChangeProposal, pk=pk)
    if not proposal.has_edit_admin(request.gooseuser):
        return forbidden(request)

    if request.method == "POST":
        try:
            proposal.try_delete()
            if ItemChangeProposal.open_proposals().count() == 0:
                NOTIFICATION_TYPES["itemchanges"].dismiss()
            messages.success(request, f"Succesfully deleted {proposal}")
        except ItemChangeError as e:
            messages.error(request, e.message)
        return HttpResponseRedirect(reverse("item-change-list"))
    else:
        return render(
            request,
            "items/item_change/item_change_confirm_delete.html",
            {"itemchangeproposal": proposal},
        )
