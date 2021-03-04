import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Union

from allauth.socialaccount.models import SocialAccount
from bravado.client import SwaggerClient
from bravado.exception import HTTPError
from bravado.requests_client import RequestsClient
from bravado.swagger_model import load_file
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
from goosetools.venmo.forms import DepositForm, TransferForm, WithdrawForm

swagger_file = load_file("goosetools/venmo/swagger.yml")


class VenmoUserBalance:
    def __init__(
        self, balance: int, available_balance: int, net_pending_change: int
    ) -> None:
        self.balance = balance
        self.available_balance = available_balance
        self.net_pending_change = net_pending_change


class VenmoInterface(ABC):
    @abstractmethod
    def user_balance(self, discord_uid: str) -> VenmoUserBalance:
        pass


class FogVenmo(VenmoInterface):
    def __init__(self) -> None:
        super().__init__()
        self._client = FogVenmo._make_swagger_client()

    @staticmethod
    def _make_swagger_client(use_models=True):
        host = settings.VENMO_HOST_URL
        requests_client = RequestsClient()
        api_token_header_name = swagger_file["securityDefinitions"]["api_key"]["name"]
        requests_client.set_api_key(
            host,
            settings.VENMO_API_TOKEN,
            param_name=api_token_header_name,
            param_in="header",
        )
        swagger_file["host"] = settings.VENMO_HOST_URL
        swagger_file["basePath"] = settings.VENMO_BASE_PATH
        return SwaggerClient.from_spec(
            swagger_file, http_client=requests_client, config={"use_models": use_models}
        )

    def user_balance(self, discord_uid: str) -> VenmoUserBalance:
        venmo_user_balance_future = self._client.users.getUserBalance(
            discordId=discord_uid,
        )
        balance_result = venmo_user_balance_future.response().result
        return VenmoUserBalance(
            balance=balance_result.balance,
            available_balance=balance_result.availableBalance,
            net_pending_change=balance_result.netPendingChange,
        )


def venmo_client(use_models=True):
    host = settings.VENMO_HOST_URL
    requests_client = RequestsClient()
    api_token_header_name = swagger_file["securityDefinitions"]["api_key"]["name"]
    requests_client.set_api_key(
        host,
        settings.VENMO_API_TOKEN,
        param_name=api_token_header_name,
        param_in="header",
    )
    swagger_file["host"] = settings.VENMO_HOST_URL
    swagger_file["basePath"] = settings.VENMO_BASE_PATH
    return SwaggerClient.from_spec(
        swagger_file, http_client=requests_client, config={"use_models": use_models}
    )


def dashboard(request, gooseuser):
    discord_uid = gooseuser.discord_uid()
    venmo_user_balance = FogVenmo().user_balance(discord_uid)
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


def lookup_gooseuser_and_cache(discord_id_to_gooseuser, discord_id_with_brackets):
    if discord_id_with_brackets not in discord_id_to_gooseuser:
        stripped_uid = re.sub("[^0-9]", "", discord_id_with_brackets)
        try:
            sa = SocialAccount.objects.get(uid=stripped_uid)
            discord_id_to_gooseuser[discord_id_with_brackets] = sa.user.gooseuser
        except SocialAccount.DoesNotExist:
            discord_id_to_gooseuser[discord_id_with_brackets] = False

    return discord_id_to_gooseuser[discord_id_with_brackets]


def parse_transactions(discord_id_to_gooseuser, ts, resulting_transactions):
    for row in ts:
        source_gooseuser = lookup_gooseuser_and_cache(
            discord_id_to_gooseuser, row["source_discord_id"]
        )
        if source_gooseuser:
            row["source_discord_id"] = source_gooseuser.display_name()
            row["source_gooseuser_id"] = source_gooseuser.id

        target_gooseuser = lookup_gooseuser_and_cache(
            discord_id_to_gooseuser, row["target_discord_id"]
        )
        if target_gooseuser:
            row["target_discord_id"] = target_gooseuser.display_name()
            row["target_gooseuser_id"] = target_gooseuser.id

        pattern = re.compile(r"(<@![0-9]+>)")
        pre_notes = row["note"]
        for discord_id in re.findall(pattern, pre_notes):
            gooseuser = lookup_gooseuser_and_cache(discord_id_to_gooseuser, discord_id)
            if gooseuser:
                row["note"] = row["note"].replace(discord_id, gooseuser.display_name())
        resulting_transactions[row["transaction_id"]] = row


def other_user_transactions_list(request, pk: int):
    gooseuser = get_object_or_404(GooseUser, pk=pk)
    return transactions_list(gooseuser)


def transactions_list(gooseuser: GooseUser):
    venmo_server_client = venmo_client(use_models=False)
    discord_uid = f"<@!{gooseuser.discord_uid()}>"
    targeted_at_user = (
        venmo_server_client.transactions.listTransactions(target_discord_id=discord_uid)
        .response()
        .result
    )
    discord_id_to_gooseuser: Dict[str, Union[GooseUser, bool]] = {}
    resulting_transactions: Dict[str, Any] = {}
    parse_transactions(
        discord_id_to_gooseuser, targeted_at_user, resulting_transactions
    )
    all_users_transactions = sorted(
        resulting_transactions.values(),
        key=lambda row: row["updatedAt"].timestamp(),
        reverse=True,
    )
    return JsonResponse({"result": all_users_transactions})


@has_perm(perm=VENMO_ADMIN)
def pending_list(request):
    venmo_server_client = venmo_client(use_models=False)
    pending_transactions = (
        venmo_server_client.transactions.listTransactions(transaction_status="pending")
        .response()
        .result
    )
    discord_id_to_gooseuser: Dict[str, Union[GooseUser, bool]] = {}
    resulting_transactions: Dict[str, Any] = {}
    parse_transactions(
        discord_id_to_gooseuser, pending_transactions, resulting_transactions
    )
    return JsonResponse({"result": list(resulting_transactions.values())})


def withdraw(request):
    if request.method == "POST":
        form = WithdrawForm(request.POST)
        if form.is_valid():
            venmo_server_client = venmo_client()
            discord_uid = f"<@!{request.gooseuser.discord_uid()}>"
            try:
                withdraw_request = venmo_server_client.withdrawals.createWithdrawal(
                    discordId=discord_uid, body={"value": form.cleaned_data["quantity"]}
                )
                withdraw_request.response()
                return HttpResponseRedirect(reverse("venmo:dashboard"))
            except HTTPError as e:
                if (
                    hasattr(e, "response")
                    and hasattr(e.response, "json")
                    and "message" in e.response.json()
                ):
                    message = e.response.json()["message"]
                    messages.error(request, message)

    else:
        form = WithdrawForm()

    return render(request, "venmo/withdraw.html", {"form": form})


def transfer(request):
    if request.method == "POST":
        form = TransferForm(request.POST)
        if form.is_valid():
            try:
                venmo_server_client = venmo_client()
                discord_uid = f"<@!{request.gooseuser.discord_uid()}>"
                to_discord_uid = form.cleaned_data["user"].discord_uid()
                transfer_request = venmo_server_client.transfers.transferToUser(
                    discordId=discord_uid,
                    toDiscordId=to_discord_uid,
                    body={"value": form.cleaned_data["quantity"]},
                )
                transfer_request.response()
                return HttpResponseRedirect(reverse("venmo:dashboard"))
            except HTTPError as e:
                if (
                    hasattr(e, "response")
                    and hasattr(e.response, "json")
                    and "message" in e.response.json()
                ):
                    message = e.response.json()["message"]
                    messages.error(request, message)
    else:
        form = TransferForm()

    return render(request, "venmo/transfer.html", {"form": form})


def deposit(request):
    if request.method == "POST":
        form = DepositForm(request.POST)
        if form.is_valid():
            try:
                venmo_server_client = venmo_client()
                discord_uid = f"<@!{request.gooseuser.discord_uid()}>"
                deposit_request = venmo_server_client.deposits.createDeposit(
                    discordId=discord_uid,
                    body={
                        "value": form.cleaned_data["quantity"],
                        "note": form.cleaned_data["note"],
                    },
                )
                deposit_request.response()
                return HttpResponseRedirect(reverse("venmo:dashboard"))
            except HTTPError as e:
                if (
                    hasattr(e, "response")
                    and hasattr(e.response, "json")
                    and "message" in e.response.json()
                ):
                    message = e.response.json()["message"]
                    messages.error(request, message)
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
        venmo_server_client = venmo_client()
        update_request = venmo_server_client.transactions.updateTransaction(
            transactionId=str(transaction_id),
            body={"transaction_status": new_status},
        )
        update_request.response()
        return HttpResponse()
    except HTTPError as e:
        message = "Unknown error with venmo."
        if (
            hasattr(e, "response")
            and hasattr(e.response, "json")
            and "message" in e.response.json()
        ):
            message = e.response.json()["message"]
        return HttpResponseBadRequest(message)
