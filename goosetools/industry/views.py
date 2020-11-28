import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http.response import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from goosetools.industry.forms import ShipOrderForm
from goosetools.industry.models import ShipOrder
from goosetools.industry.serializers import ShipOrderSerializer

login_url = reverse_lazy("discord_login")


def forbidden(request):
    messages.error(request, "You are forbidden to access this.")
    return render(request, "contracts/403.html")


@transaction.atomic
@login_required(login_url=login_url)
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


def generate_random_string():
    return get_random_string(6)


@transaction.atomic
@login_required(login_url=login_url)
def shiporders_create(request):
    if request.method == "POST":
        form = ShipOrderForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            username = data["recipient_character"].discord_user.username

            uid = f"{username}-{generate_random_string()}"
            ship_order = ShipOrder.objects.create(
                ship=data["ship"],
                recipient_character=data["recipient_character"],
                quantity=data["quantity"],
                payment_method=data["payment_method"],
                notes=data["notes"],
                uid=uid,
                state="not_started",
                assignee=None,
                created_at=timezone.now(),
                contract_made=False,
            )
            return HttpResponseRedirect(
                reverse("industry:shiporders_contract_confirm", args=[ship_order.pk])
            )
    else:
        form = ShipOrderForm(
            initial={"recipient_character": request.user.default_character}
        )
        form.fields["recipient_character"].queryset = request.user.characters()

    return render(request, "industry/shiporders/create.html", {"form": form})


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
        if ship_order.assignee is None:
            ship_order.assignee = request.user
            ship_order.save()
            claim_status = "claimed"
        else:
            claim_status = "already_claimed"
        return Response(
            {
                "status": claim_status,
                "assignee": ship_order.assignee.pk,
                "assignee_name": ship_order.assignee.discord_username(),
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


@login_required(login_url=login_url)
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
                "request_user_pk": request.user.pk,
                "request_user_character_pks": [
                    char.pk for char in request.user.characters()
                ],
            }
        },
    )
