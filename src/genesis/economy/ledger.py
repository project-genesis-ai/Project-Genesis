from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    transaction_id: str
    tick: int
    account: str
    amount: float
    memo: str = ""

    def __post_init__(self) -> None:
        if not self.transaction_id.strip() or not self.account.strip() or self.tick < 0:
            raise ValueError("invalid ledger entry")
        if self.amount == 0.0:
            raise ValueError("ledger entry amount cannot be zero")


@dataclass(frozen=True, slots=True)
class LedgerTransaction:
    transaction_id: str
    tick: int
    entries: tuple[LedgerEntry, ...]
    memo: str = ""

    def __post_init__(self) -> None:
        if not self.transaction_id.strip() or self.tick < 0 or len(self.entries) < 2:
            raise ValueError("a ledger transaction requires at least two entries")
        if any(entry.transaction_id != self.transaction_id or entry.tick != self.tick for entry in self.entries):
            raise ValueError("ledger entry metadata must match transaction")
        if abs(sum(entry.amount for entry in self.entries)) > 1e-9:
            raise ValueError("ledger transaction is not balanced")


@dataclass(slots=True)
class DoubleEntryLedger:
    """Append-only balanced ledger; positive amounts increase an account balance."""

    transactions: list[LedgerTransaction] = field(default_factory=list)
    balances: dict[str, float] = field(default_factory=dict)

    def post(self, transaction: LedgerTransaction) -> None:
        if any(item.transaction_id == transaction.transaction_id for item in self.transactions):
            raise ValueError(f"duplicate transaction: {transaction.transaction_id}")
        if self.transactions and transaction.tick < self.transactions[-1].tick:
            raise ValueError("transactions must be chronological")
        for entry in transaction.entries:
            self.balances[entry.account] = self.balances.get(entry.account, 0.0) + entry.amount
        self.transactions.append(transaction)

    def transfer(self, transaction_id: str, tick: int, source: str, destination: str, amount: float, memo: str = "") -> LedgerTransaction:
        if not source.strip() or not destination.strip() or source == destination or amount <= 0.0:
            raise ValueError("invalid transfer")
        transaction = LedgerTransaction(
            transaction_id,
            tick,
            (
                LedgerEntry(transaction_id, tick, source, -amount, memo),
                LedgerEntry(transaction_id, tick, destination, amount, memo),
            ),
            memo,
        )
        self.post(transaction)
        return transaction

    def balance(self, account: str) -> float:
        if not account.strip():
            raise ValueError("account cannot be empty")
        return self.balances.get(account, 0.0)

    def total_assets(self) -> float:
        return sum(self.balances.values())
