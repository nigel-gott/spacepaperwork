import json
from random import randint
from typing import Any, Dict

from django.contrib import messages
from django.db import transaction
from django.db.models.aggregates import Max
from django.db.models.functions import Coalesce
from django.http.request import HttpRequest
from django.http.response import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from rest_framework import mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from goosetools.industry.forms import ShipOrderForm
from goosetools.industry.models import Ship, ShipOrder, to_isk
from goosetools.industry.serializers import ShipOrderSerializer
from goosetools.users.models import Character, GooseUser


def forbidden(request):
    messages.error(request, "You are forbidden to access this.")
    return render(request, "contracts/403.html")


@transaction.atomic
def shiporders_contract_confirm(request, pk):
    ship_order = get_object_or_404(ShipOrder, pk=pk)
    if ship_order.recipient_character.discord_user != request.user.discord_user:
        return HttpResponseForbidden()
    if request.method == "POST":
        ship_order.contract_made = True
        ship_order.save()
        return HttpResponseRedirect(reverse("industry:shiporders_view"))
    else:
        return render(
            request,
            "industry/shiporders/contract_confirm.html",
            {"ship_order": ship_order},
        )


def random_with_n_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return randint(range_start, range_end)


def generate_contract_code(user):
    for _ in range(100):
        possible_id = f"{user.discord_username()}-{random_with_n_digits(6)}"
        if ShipOrder.objects.filter(uid=possible_id).count() == 0:
            return possible_id
    raise Exception(f"Failed to create a unique random contract code for {user}")


def calculate_blocked_until_for_order(ship, recieving_user):
    order_limit_group = ship.order_limit_group
    if order_limit_group:
        limit_period = timezone.timedelta(days=order_limit_group.days_between_orders)
        limit = timezone.now() - limit_period
        prev_order_start = (
            ShipOrder.objects.filter(
                recipient_character__discord_user__gooseuser=recieving_user,
                payment_method="free",
                contract_made=True,
                ship__order_limit_group=order_limit_group,
            )
            .annotate(order_valid_from=Coalesce("blocked_until", "created_at"))
            .filter(order_valid_from__gt=limit)
            .aggregate(prev_order_start=Max("order_valid_from"))["prev_order_start"]
        )
        if prev_order_start:
            blocked_until = prev_order_start + limit_period
            return (
                blocked_until,
                f"You have already ordered a ship in the '{order_limit_group.name}' category within the last {order_limit_group.days_between_orders} days, this order will be blocked until {blocked_until}.",
            )
    return None, None


def create_ship_order(
    ship: Ship,
    recieving_user: GooseUser,
    recipient_character: Character,
    quantity: int,
    payment_method: str,
    notes: str,
    request: HttpRequest,
) -> ShipOrder:
    uid = generate_contract_code(request.user)

    price = None
    payment_taken = False
    blocked_until = None
    if payment_method in {"eggs", "isk"}:
        if ship.valid_price():
            if payment_method == "eggs":
                price = ship.eggs_price
            else:
                price = ship.isk_price
    else:
        if payment_method == "free":
            blocked_until, message = calculate_blocked_until_for_order(
                ship, recieving_user
            )
            if message:
                messages.warning(request, message)
        payment_taken = True

    return ShipOrder.objects.create(
        ship=ship,
        recipient_character=recipient_character,
        quantity=quantity,
        payment_method=payment_method,
        notes=notes,
        uid=uid,
        state="not_started",
        assignee=None,
        created_at=timezone.now(),
        blocked_until=blocked_until,
        contract_made=False,
        price=price,
        payment_taken=payment_taken,
    )


def validate_order(request, ship, payment_method, quantity, isk_price, eggs_price):
    if ship.eggs_price != eggs_price or ship.isk_price != isk_price:
        messages.error(
            request,
            f"The prices for the ship have changed since you opened the order form, please order again the prices have been updated. {ship.eggs_price} vs {eggs_price} and {ship.isk_price} vs {isk_price}",
        )
    elif not ship.free and payment_method == "free":
        messages.error(
            request,
            "This ship is not free, you must select eggs or isk as a payment method.",
        )
    elif payment_method == "free" and quantity > 1:
        messages.error(request, "You cannot order more than free ship at one time.")
    else:
        return True
    return False


def populate_ship_data(user) -> Dict[str, Any]:
    ship_data = {}
    ships = Ship.objects.all()
    for ship in ships:
        current_ship_data: Dict[str, Any] = {
            "free": ship.free,
            "tech_level": ship.tech_level,
            "isk_price": ship.isk_price and ship.isk_price.amount,
            "eggs_price": ship.eggs_price and ship.eggs_price.amount,
            "valid_price": ship.valid_price(),
        }
        blocked_until, _ = calculate_blocked_until_for_order(ship, user)
        if blocked_until is not None:
            current_ship_data["blocked_until"] = blocked_until.strftime(
                "%Y-%m-%d %H:%M"
            )
        if ship.order_limit_group:
            current_ship_data["order_limit_group"] = {
                "name": ship.order_limit_group.name,
                "days_between_orders": ship.order_limit_group.days_between_orders,
            }
        ship_data[ship.name] = current_ship_data
    return ship_data


@transaction.atomic
def shiporders_create(request):
    if request.method == "POST":
        form = ShipOrderForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            ship = data["ship"]
            payment_method = data["payment_method"]
            quantity = data["quantity"]
            isk_price = data["isk_price"]
            eggs_price = data["eggs_price"]
            if validate_order(
                request,
                ship,
                payment_method,
                quantity,
                isk_price and to_isk(isk_price),
                eggs_price and to_isk(eggs_price),
            ):
                ship_order = create_ship_order(
                    ship,
                    request.user,
                    data["recipient_character"],
                    quantity,
                    payment_method,
                    data["notes"],
                    request,
                )
                return HttpResponseRedirect(
                    reverse(
                        "industry:shiporders_contract_confirm", args=[ship_order.pk]
                    )
                )
    else:
        form = ShipOrderForm(
            initial={"recipient_character": request.user.default_character}
        )
        form.fields["recipient_character"].queryset = request.user.characters()

    ship_data = populate_ship_data(request.user)
    return render(
        request,
        "industry/shiporders/create.html",
        {"form": form, "ship_data": ship_data},
    )


class ShipOrderViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet
):
    queryset = (
        ShipOrder.objects.filter(contract_made=True).all().order_by("-created_at")
    )
    serializer_class = ShipOrderSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def transition(self, request, pk=None):
        ship_order = self.get_object()
        if ship_order.assignee != request.user:
            return Response(status.HTTP_403_FORBIDDEN)
        else:
            body_unicode = request.body.decode("utf-8")
            body = json.loads(body_unicode)
            transition = body["transition"]
            transitions = ship_order.availible_transitions()
            if transition not in transitions.keys():
                return Response(status.HTTP_403_FORBIDDEN)
            else:
                ship_order.state = transitions[transition].target
                ship_order.full_clean()
                ship_order.save()
                return Response(
                    {
                        "new_state": ship_order.state,
                        "availible_transition_names": ship_order.availible_transition_names(),
                    }
                )

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def claim(self, request, pk=None):
        ship_order = self.get_object()
        if ship_order.currently_blocked():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if ship_order.assignee is None:
            ship_order.assignee = request.user
            ship_order.save()
            claim_status = "claimed"
            uid = ship_order.uid
        else:
            claim_status = "already_claimed"
            uid = None
        return Response(
            {
                "status": claim_status,
                "assignee": ship_order.assignee.pk,
                "assignee_name": ship_order.assignee.discord_username(),
                "uid": uid,
            }
        )

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def unclaim(self, request, pk=None):
        ship_order = self.get_object()
        if ship_order.assignee is None:
            return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            ship_order.assignee = None
            ship_order.save()
            return Response(
                {
                    "status": "unclaimed",
                }
            )

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def paid(self, request, pk=None):
        ship_order = self.get_object()
        if ship_order.assignee != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            ship_order.payment_taken = True
            ship_order.full_clean()
            ship_order.save()
            return Response({"payment_taken": ship_order.payment_actually_taken()})

    @action(detail=True, methods=["PUT"])
    @transaction.atomic
    # pylint: disable=unused-argument
    def manual_price(self, request, pk=None):
        ship_order = self.get_object()
        if ship_order.assignee != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            body_unicode = request.body.decode("utf-8")
            body = json.loads(body_unicode)
            if "manual_price" not in body or not isinstance(body["manual_price"], int):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            ship_order.price = to_isk(body["manual_price"])
            ship_order.full_clean()
            ship_order.save()
            return Response(
                {
                    "price": ship_order.price.amount,
                    "needs_manual_price": ship_order.needs_manual_price(),
                }
            )


def shiporders_view(request):
    return render(
        request,
        "industry/shiporders/view.html",
        context={
            "page_data": {
                "has_industry_permission": request.user.has_perm(
                    "industry.change_shiporder"
                ),
                "request_user_discord_username": request.user.discord_username(),
                "request_discord_user_pk": request.user.discord_user.pk,
                "request_user_pk": request.user.pk,
                "request_user_character_pks": [
                    char.pk for char in request.user.characters()
                ],
            }
        },
    )
