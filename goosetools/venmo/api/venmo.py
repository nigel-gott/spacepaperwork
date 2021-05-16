from abc import ABC, abstractmethod
from datetime import datetime
from typing import List


# pylint: disable=too-many-instance-attributes
class VenmoTransaction(dict):
    def __init__(
        self,
        transaction_id: str,
        source_discord_id: str,
        source_gooseuser_id: int,
        target_discord_id: str,
        target_gooseuser_id: int,
        note: str,
        value: int,
        transaction_type: str,
        transaction_status: str,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        dict.__init__(
            transaction_id=transaction_id,
            source_discord_id=source_discord_id,  # Display Name or just Id
            source_gooseuser_id=source_gooseuser_id,  # Optional
            target_discord_id=target_discord_id,  # Display Name or just Id
            target_gooseuser_id=target_gooseuser_id,  # Optional
            note=note,
            value=value,
            transaction_type=transaction_type,  # deposit, withdrawal, credit, debit
            transaction_status=(
                transaction_status  # pending, complete, rejected, cancelled
            ),
            created_at=created_at,  # datetime str
            updated_at=updated_at,
        )


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

    @abstractmethod
    def user_transactions(self, discord_uid: str) -> List[VenmoTransaction]:
        pass

    @abstractmethod
    def pending_transactions(self) -> List[VenmoTransaction]:
        pass

    @abstractmethod
    def withdraw(self, discord_uid: str, withdrawal_quantity: int) -> None:
        pass

    @abstractmethod
    def deposit(self, discord_uid: str, deposit_quantity: int, note: str) -> None:
        pass

    @abstractmethod
    def transfer(
        self, from_discord_uid: str, to_discord_uid: str, transfer_quantity: int
    ) -> None:
        pass

    @abstractmethod
    def update_transaction(self, transaction_id: str, new_status: str) -> None:
        pass


class VenmoError(Exception):
    def __init__(self, message) -> None:
        super().__init__()
        self.message = message
