import logging
import re
from typing import Dict, List, Union

from allauth.socialaccount.models import SocialAccount
from bravado.client import SwaggerClient
from bravado.exception import HTTPError
from bravado.requests_client import RequestsClient
from bravado.swagger_model import load_file
from django.conf import settings

from goosetools.users.models import GooseUser
from goosetools.venmo.api.venmo import (
    VenmoError,
    VenmoInterface,
    VenmoTransaction,
    VenmoUserBalance,
)

swagger_file = load_file("goosetools/venmo/swagger.yml")

logger = logging.getLogger(__name__)


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
        else:
            row["source_gooseuser_id"] = None

        target_gooseuser = lookup_gooseuser_and_cache(
            discord_id_to_gooseuser, row["target_discord_id"]
        )
        if target_gooseuser:
            row["target_discord_id"] = target_gooseuser.display_name()
            row["target_gooseuser_id"] = target_gooseuser.id
        else:
            row["target_gooseuser_id"] = None

        pattern = re.compile(r"(<@![0-9]+>)")
        pre_notes = row["note"]
        for discord_id in re.findall(pattern, pre_notes):
            gooseuser = lookup_gooseuser_and_cache(discord_id_to_gooseuser, discord_id)
            if gooseuser:
                row["note"] = row["note"].replace(discord_id, gooseuser.display_name())
        resulting_transactions[row["transaction_id"]] = VenmoTransaction(
            transaction_id=row["transaction_id"],
            source_discord_id=row["source_discord_id"],
            source_gooseuser_id=row["source_gooseuser_id"],
            target_discord_id=row["target_discord_id"],
            target_gooseuser_id=row["target_gooseuser_id"],
            note=row["note"],
            value=row["value"],
            transaction_type=row["transaction_type"],
            transaction_status=row["transaction_status"],
            created_at=row["createdAt"],
            updated_at=row["updatedAt"],
        )


def fog_venmo_client(use_models=True):
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


class FogVenmo(VenmoInterface):
    def user_balance(self, discord_uid: str) -> VenmoUserBalance:
        venmo_user_balance_future = fog_venmo_client().users.getUserBalance(
            discordId=discord_uid,
        )
        balance_result = venmo_user_balance_future.response().result
        return VenmoUserBalance(
            balance=balance_result.balance,
            available_balance=balance_result.availableBalance,
            net_pending_change=balance_result.netPendingChange,
        )

    def user_transactions(self, discord_uid: str) -> List[VenmoTransaction]:
        discord_uid = f"<@!{discord_uid}>"
        return FogVenmo._transactions_with_filter(target_discord_id=discord_uid)

    def pending_transactions(self) -> List[VenmoTransaction]:
        return FogVenmo._transactions_with_filter(transaction_status="pending")

    def withdraw(self, discord_uid: str, withdrawal_quantity: int) -> None:
        venmo_server_client = fog_venmo_client()
        discord_uid = f"<@!{discord_uid}>"
        try:
            withdraw_request = venmo_server_client.withdrawals.createWithdrawal(
                discordId=discord_uid, body={"value": withdrawal_quantity}
            )
            withdraw_request.response()
        except HTTPError as e:
            message = "Unknown error with venmo."
            if (
                hasattr(e, "response")
                and hasattr(e.response, "json")
                and "message" in e.response.json()
            ):
                message = e.response.json()["message"]
            raise VenmoError(message=message)

    def deposit(self, discord_uid: str, deposit_quantity: int, note: str):
        try:
            venmo_server_client = fog_venmo_client()
            discord_uid = f"<@!{discord_uid}>"
            deposit_request = venmo_server_client.deposits.createDeposit(
                discordId=discord_uid,
                body={
                    "value": deposit_quantity,
                    "note": note,
                },
            )
            deposit_request.response()
        except HTTPError as e:
            message = "Unknown error with venmo."
            if (
                hasattr(e, "response")
                and hasattr(e.response, "json")
                and "message" in e.response.json()
            ):
                message = e.response.json()["message"]
            raise VenmoError(message)

    def transfer(
        self, from_discord_uid: str, to_discord_uid: str, transfer_quantity: int
    ) -> None:
        try:
            venmo_server_client = fog_venmo_client()
            discord_uid = f"<@!{from_discord_uid}>"
            transfer_request = venmo_server_client.transfers.transferToUser(
                discordId=discord_uid,
                toDiscordId=to_discord_uid,
                body={"value": transfer_quantity},
            )
            transfer_request.response()
        except HTTPError as e:
            message = "Unknown error with venmo."
            if (
                hasattr(e, "response")
                and hasattr(e.response, "json")
                and "message" in e.response.json()
            ):
                message = e.response.json()["message"]
            raise VenmoError(message)

    def update_transaction(self, transaction_id: str, new_status: str) -> None:
        try:
            venmo_server_client = fog_venmo_client()
            update_request = venmo_server_client.transactions.updateTransaction(
                transactionId=str(transaction_id),
                body={"transaction_status": new_status},
            )
            update_request.response()
        except HTTPError as e:
            message = "Unknown error with venmo."
            if (
                hasattr(e, "response")
                and hasattr(e.response, "json")
                and "message" in e.response.json()
            ):
                message = e.response.json()["message"]
            raise VenmoError(message)

    @staticmethod
    def _transactions_with_filter(**kwargs) -> List[VenmoTransaction]:
        client = fog_venmo_client(use_models=False)
        transactions = client.transactions.listTransactions(**kwargs)
        targeted_at_user = transactions.response().result
        discord_id_to_gooseuser: Dict[str, Union[GooseUser, bool]] = {}
        resulting_transactions: Dict[str, VenmoTransaction] = {}
        parse_transactions(
            discord_id_to_gooseuser, targeted_at_user, resulting_transactions
        )
        return sorted(
            resulting_transactions.values(),
            key=lambda t: t.updated_at.timestamp(),
            reverse=True,
        )
