from typing import List

from goosetools.venmo.api.venmo import (
    VenmoError,
    VenmoInterface,
    VenmoTransaction,
    VenmoUserBalance,
)
from goosetools.venmo.models import VirtualCurrency


class SpaceVenmo(VenmoInterface):
    def __init__(self, currency: VirtualCurrency) -> None:
        super().__init__()
        self.currency = currency

    def user_balance(self, discord_uid: str) -> VenmoUserBalance:
        # Query balance account for currency
        # Query pending withdrawal account
        raise VenmoError("Not Implemented")

    def user_transactions(self, discord_uid: str) -> List[VenmoTransaction]:
        # Query all transactions for player account
        raise VenmoError("Not Implemented")

    def pending_transactions(self) -> List[VenmoTransaction]:
        # Query all pending withdrawal accounts?
        # Query all deposit accounts?
        raise VenmoError("Not Implemented")

    def withdraw(self, discord_uid: str, withdrawal_quantity: int) -> None:
        # Create tran
        raise VenmoError("Not Implemented")

    def deposit(self, discord_uid: str, deposit_quantity: int, note: str) -> None:
        raise VenmoError("Not Implemented")

    def transfer(
        self, from_discord_uid: str, to_discord_uid: str, transfer_quantity: int
    ) -> None:
        raise VenmoError("Not Implemented")

    def update_transaction(self, transaction_id: str, new_status: str) -> None:
        raise VenmoError("Not Implemented")
