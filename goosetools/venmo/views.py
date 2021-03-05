from django.conf import settings
from django.contrib import messages
from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from goosetools.users.models import VENMO_ADMIN, GooseUser, has_perm
from goosetools.venmo.api.fog_venmo import FogVenmo
from goosetools.venmo.api.space_venmo import SpaceVenmo
from goosetools.venmo.api.venmo import VenmoError, VenmoUserBalance
from goosetools.venmo.forms import DepositForm, TransferForm, WithdrawForm


def dashboard(request, gooseuser):
    discord_uid = gooseuser.discord_uid()
    try:
        venmo_user_balance = venmo_api().user_balance(discord_uid)
    except VenmoError:
        messages.error(request, "Failed to load your balance from venmo.")
        venmo_user_balance = VenmoUserBalance(0, 0, 0)
    context = {
        "page_data": {
            "gooseuser_id": gooseuser.id,
            "site_prefix": f"/{request.site_prefix}",
        },
        "gooseuser": gooseuser,
        "venmo_user_balance": venmo_user_balance,
    }
    return render(request, "venmo/dashboard.html", context=context)


def other_dashboard(request, pk: int):
    gooseuser = get_object_or_404(GooseUser, pk=pk)
    return dashboard(request, gooseuser)


def own_dashboard(request):
    return dashboard(request, request.gooseuser)


@has_perm(perm=VENMO_ADMIN)
def pending(request):
    return render(
        request,
        "venmo/pending.html",
        {
            "page-data": {},
        },
    )


def other_user_transactions_list(request, pk: int):
    gooseuser = get_object_or_404(GooseUser, pk=pk)
    return transactions_list(gooseuser)


def transactions_list(gooseuser: GooseUser):
    return JsonResponse(
        {"result": venmo_api().user_transactions(gooseuser.discord_uid())}
    )


@has_perm(perm=VENMO_ADMIN)
def pending_list(request):
    return JsonResponse({"result": venmo_api().pending_transactions()})


def venmo_api():
    if settings.GOOSEFLOCK_FEATURES:
        return FogVenmo()
    else:
        return SpaceVenmo()


def withdraw(request):
    if request.method == "POST":
        form = WithdrawForm(request.POST)
        if form.is_valid():
            try:
                venmo_api().withdraw(
                    request.gooseuser.discord_uid(), form.cleaned_data["quantity"]
                )
                return HttpResponseRedirect(reverse("venmo:dashboard"))
            except VenmoError as e:
                messages.error(request, e.message)
    else:
        form = WithdrawForm()

    return render(request, "venmo/withdraw.html", {"form": form})


def transfer(request):
    if request.method == "POST":
        form = TransferForm(request.POST)
        if form.is_valid():
            try:
                venmo_api().transfer(
                    request.gooseuser.discord_uid(),
                    form.cleaned_data["user"],
                    form.cleaned_data["quantity"],
                )
                return HttpResponseRedirect(reverse("venmo:dashboard"))
            except VenmoError as e:
                messages.error(request, e.message)
    else:
        form = TransferForm()

    return render(request, "venmo/transfer.html", {"form": form})


def deposit(request):
    if request.method == "POST":
        form = DepositForm(request.POST)
        if form.is_valid():
            try:
                venmo_api().deposit(
                    request.gooseuser.discord_uid(),
                    form.cleaned_data["quantity"],
                    form.cleaned_data["note"],
                )
                return HttpResponseRedirect(reverse("venmo:dashboard"))
            except VenmoError as e:
                messages.error(request, e.message)
    else:
        form = DepositForm()

    return render(request, "venmo/deposit.html", {"form": form})


@has_perm(perm=VENMO_ADMIN)
def approve_transaction(request, pk: int):
    return update_transaction(request, pk, "complete")


@has_perm(perm=VENMO_ADMIN)
def deny_transaction(request, pk: int):
    return update_transaction(request, pk, "rejected")


def update_transaction(request, transaction_id: int, new_status: str):
    if request.method != "PUT":
        return HttpResponseForbidden()
    try:
        venmo_api().update_transaction(str(transaction_id), new_status)
        return HttpResponse()
    except VenmoError as e:
        messages.error(request, e.message)
        return HttpResponseBadRequest()
