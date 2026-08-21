from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Wallet:
    owner_id: str
    balance: float = 0.0

    def __post_init__(self) -> None:
        if not self.owner_id.strip() or self.balance < 0:
            raise ValueError("invalid wallet")

    def credit(self, amount: float) -> None:
        if amount < 0:
            raise ValueError("amount cannot be negative")
        self.balance += amount

    def debit(self, amount: float) -> bool:
        if amount < 0:
            raise ValueError("amount cannot be negative")
        if amount > self.balance:
            return False
        self.balance -= amount
        return True

    def transfer_to(self, recipient: Wallet, amount: float) -> bool:
        if not self.debit(amount):
            return False
        recipient.credit(amount)
        return True
