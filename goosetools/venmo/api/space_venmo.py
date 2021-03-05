from typing import List

from goosetools.venmo.api.venmo import (
    VenmoError,
    VenmoInterface,
    VenmoTransaction,
    VenmoUserBalance,
)


class SpaceVenmo(VenmoInterface):
    def user_balance(self, discord_uid: str) -> VenmoUserBalance:
        raise VenmoError("Not Implemented")

    def user_transactions(self, discord_uid: str) -> List[VenmoTransaction]:
        raise VenmoError("Not Implemented")

    def pending_transactions(self) -> List[VenmoTransaction]:
        raise VenmoError("Not Implemented")

    def withdraw(self, discord_uid: str, withdrawal_quantity: int) -> None:
        raise VenmoError("Not Implemented")

    def deposit(self, discord_uid: str, deposit_quantity: int, note: str) -> None:
        raise VenmoError("Not Implemented")

    def transfer(
        self, from_discord_uid: str, to_discord_uid: str, transfer_quantity: int
    ) -> None:
        raise VenmoError("Not Implemented")

    def update_transaction(self, transaction_id: str, new_status: str) -> None:
        raise VenmoError("Not Implemented")
