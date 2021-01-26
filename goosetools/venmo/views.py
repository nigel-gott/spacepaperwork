import re
from typing import Any, Dict, Union

from allauth.socialaccount.models import SocialAccount
from bravado.client import SwaggerClient
from bravado.requests_client import RequestsClient
from bravado.swagger_model import load_file
from django.conf import settings
from django.http.response import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from goosetools.users.models import GooseUser
from goosetools.venmo.forms import DepositForm, TransferForm, WithdrawForm

swagger_file = load_file("goosetools/venmo/swagger.yml")


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
    return SwaggerClient.from_spec(
        swagger_file, http_client=requests_client, config={"use_models": use_models}
    )


def dashboard(request, gooseuser):
    venmo_server_client = venmo_client()
    discord_uid = gooseuser.discord_uid()
    venmo_user_balance_future = venmo_server_client.users.getUserBalance(
        discordId=discord_uid,
    )
    venmo_user_balance = venmo_user_balance_future.response().result
    return render(
        request,
        "venmo/dashboard.html",
        {
            "page_data": {
                "gooseuser_id": gooseuser.id,
                "site_prefix": f"/{settings.URL_PREFIX}",
            },
            "gooseuser": gooseuser,
            "venmo_user_balance": venmo_user_balance,
        },
    )


def other_dashboard(request, pk: int):
    gooseuser = get_object_or_404(GooseUser, pk=pk)
    return dashboard(request, gooseuser)


def own_dashboard(request):
    return dashboard(request, request.gooseuser)


def pending(request):
    if request.user.is_superuser:
        return render(
            request,
            "venmo/pending.html",
            {
                "page-data": {},
            },
        )
    else:
        return HttpResponseForbidden()


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
    sourced_by_user = (
        venmo_server_client.transactions.listTransactions(source_discord_id=discord_uid)
        .response()
        .result
    )
    targeted_at_user = (
        venmo_server_client.transactions.listTransactions(target_discord_id=discord_uid)
        .response()
        .result
    )
    discord_id_to_gooseuser: Dict[str, Union[GooseUser, bool]] = {}
    resulting_transactions: Dict[str, Any] = {}
    parse_transactions(discord_id_to_gooseuser, sourced_by_user, resulting_transactions)
    parse_transactions(
        discord_id_to_gooseuser, targeted_at_user, resulting_transactions
    )
    all_users_transactions = sorted(
        resulting_transactions.values(),
        key=lambda row: row["updatedAt"].timestamp(),
        reverse=True,
    )
    return JsonResponse({"result": all_users_transactions})


def pending_list(request):
    if request.user.is_superuser:
        venmo_server_client = venmo_client(use_models=False)
        pending_transactions = (
            venmo_server_client.transactions.listTransactions(
                transaction_status="pending"
            )
            .response()
            .result
        )
        discord_id_to_gooseuser: Dict[str, Union[GooseUser, bool]] = {}
        resulting_transactions: Dict[str, Any] = {}
        parse_transactions(
            discord_id_to_gooseuser, pending_transactions, resulting_transactions
        )
        return JsonResponse({"result": list(resulting_transactions.values())})
    else:
        return HttpResponseForbidden()


def withdraw(request):
    if request.method == "POST":
        form = WithdrawForm(request.POST)
        if form.is_valid():
            venmo_server_client = venmo_client()
            discord_uid = f"<@!{request.gooseuser.discord_uid()}>"
            withdraw_request = venmo_server_client.withdrawals.createWithdrawal(
                discordId=discord_uid, body={"value": form.cleaned_data["quantity"]}
            )
            withdraw_request.response()
            return HttpResponseRedirect(reverse("venmo:dashboard"))
    else:
        form = WithdrawForm()

    return render(request, "venmo/withdraw.html", {"form": form})


def transfer(request):
    if request.method == "POST":
        form = TransferForm(request.POST)
        if form.is_valid():
            venmo_server_client = venmo_client()
            discord_uid = f"<@!{request.gooseuser.discord_uid()}>"
            to_discord_uid = GooseUser.objects.get(
                id=form.cleaned_data["username"]
            ).discord_uid()
            transfer_request = venmo_server_client.transfers.transferToUser(
                discordId=discord_uid,
                toDiscordId=to_discord_uid,
                body={"value": form.cleaned_data["quantity"]},
            )
            transfer_request.response()
            return HttpResponseRedirect(reverse("venmo:dashboard"))
    else:
        form = TransferForm()

    return render(request, "venmo/transfer.html", {"form": form})


def deposit(request):
    if request.method == "POST":
        form = DepositForm(request.POST)
        if form.is_valid():
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
    else:
        form = DepositForm()

    return render(request, "venmo/deposit.html", {"form": form})


def approve_transaction(request, pk: int):
    return update_transaction(request, pk, "complete")


def deny_transaction(request, pk: int):
    return update_transaction(request, pk, "rejected")


def update_transaction(request, transaction_id: int, new_status: str):
    if not request.user.is_superuser or request.method != "PUT":
        return HttpResponseForbidden()
    venmo_server_client = venmo_client()
    update_request = venmo_server_client.transactions.updateTransaction(
        transactionId=str(transaction_id),
        body={"transaction_status": new_status},
    )
    update_request.response()
    return HttpResponse()
