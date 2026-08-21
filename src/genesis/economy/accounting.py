from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Money:
    """Exact monetary amount represented in the smallest currency unit."""

    minor_units: int
    currency: str = "GEN"

    def __post_init__(self) -> None:
        if not self.currency or len(self.currency) > 8:
            raise ValueError("invalid currency")

    def __add__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money(self.minor_units + other.minor_units, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money(self.minor_units - other.minor_units, self.currency)

    def _same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError("currency mismatch")


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    account: str
    amount: Money
    memo: str = ""
    transaction_id: str = ""
    tick: int = 0

    def __post_init__(self) -> None:
        if not self.account.strip() or self.tick < 0:
            raise ValueError("invalid ledger entry")


@dataclass(frozen=True, slots=True)
class LedgerTransaction:
    transaction_id: str
    tick: int
    debit_account: str
    credit_account: str
    amount: Money
    memo: str = ""

    def __post_init__(self) -> None:
        if not self.transaction_id.strip() or self.tick < 0:
            raise ValueError("invalid transaction")
        if not self.debit_account.strip() or not self.credit_account.strip() or self.debit_account == self.credit_account:
            raise ValueError("invalid accounting accounts")
        if self.amount.minor_units <= 0:
            raise ValueError("transaction amount must be positive")


@dataclass(slots=True)
class DoubleEntryLedger:
    """Balanced append-only accounting journal with deterministic transaction IDs."""

    entries: list[LedgerEntry] = field(default_factory=list)
    transactions: list[LedgerTransaction] = field(default_factory=list)

    def post(
        self,
        debit_account: str,
        credit_account: str,
        amount: Money,
        memo: str = "",
        *,
        transaction_id: str | None = None,
        tick: int = 0,
    ) -> LedgerTransaction:
        transaction = LedgerTransaction(
            transaction_id or f"tx:{tick}:{len(self.transactions)}",
            tick,
            debit_account,
            credit_account,
            amount,
            memo,
        )
        if any(item.transaction_id == transaction.transaction_id for item in self.transactions):
            raise ValueError(f"duplicate transaction: {transaction.transaction_id}")
        self.entries.extend((
            LedgerEntry(debit_account, amount, memo, transaction.transaction_id, tick),
            LedgerEntry(credit_account, Money(-amount.minor_units, amount.currency), memo, transaction.transaction_id, tick),
        ))
        self.transactions.append(transaction)
        return transaction

    def transfer(self, transaction_id: str, tick: int, source: str, destination: str, amount: float, memo: str = "") -> LedgerTransaction:
        if amount <= 0.0:
            raise ValueError("transfer amount must be positive")
        minor_units = int(round(amount * 1_000_000))
        if minor_units <= 0:
            raise ValueError("transfer amount is below ledger precision")
        return self.post(
            source,
            destination,
            Money(minor_units),
            memo,
            transaction_id=transaction_id,
            tick=tick,
        )

    def balance(self, account: str, currency: str = "GEN") -> Money:
        return Money(sum(e.amount.minor_units for e in self.entries if e.account == account and e.amount.currency == currency), currency)

    @property
    def balances(self) -> dict[str, float]:
        accounts = {entry.account for entry in self.entries}
        return {account: self.balance(account).minor_units / 1_000_000 for account in sorted(accounts)}

    def is_balanced(self, currency: str = "GEN") -> bool:
        return sum(e.amount.minor_units for e in self.entries if e.amount.currency == currency) == 0
