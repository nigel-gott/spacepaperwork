from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from goosetools.industry.forms import ShipOrderForm
from goosetools.industry.models import ShipOrder

login_url = reverse_lazy("discord_login")


def forbidden(request):
    messages.error(request, "You are forbidden to access this.")
    return render(request, "contracts/403.html")


@transaction.atomic
@login_required(login_url=login_url)
def shiporders_create(request):
    if request.method == "POST":
        form = ShipOrderForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            ShipOrder.objects.create(
                ship=data["ship"],
                recipient_character=data["recipient_character"],
                quantity=data["quantity"],
                payment_method=data["payment_method"],
                notes=data["notes"],
                state="not_started",
                assignee=None,
                created_at=timezone.now(),
            )
            return HttpResponseRedirect(reverse("industry:shiporders_view"))
    else:
        form = ShipOrderForm(
            initial={"recipient_character": request.user.default_character}
        )
        form.fields["recipient_character"].queryset = request.user.characters()

    return render(request, "industry/shiporders/create.html", {"form": form})


def ship_order_model_to_view_json(ship_order: ShipOrder) -> Dict[str, Any]:
    return {
        "assignee": ship_order.assignee or "Nobody",
        "created_at": ship_order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "payment_method": ship_order.payment_method,
        "quantity": ship_order.quantity,
        "recipient_character": ship_order.recipient_character.ingame_name,
        "ship": ship_order.ship.name,
        "state": ship_order.state,
    }


@transaction.atomic
@login_required(login_url=login_url)
def shiporders_view(request):
    ship_orders = [
        ship_order_model_to_view_json(ship_order)
        for ship_order in ShipOrder.objects.all()
    ]

    return render(
        request, "industry/shiporders/view.html", context={"ship_orders": ship_orders}
    )
