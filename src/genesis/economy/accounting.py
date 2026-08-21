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

@dataclass(slots=True)
class DoubleEntryLedger:
    """Balanced accounting journal; every posted transaction nets to zero."""
    entries: list[LedgerEntry] = field(default_factory=list)

    def post(self, debit_account: str, credit_account: str, amount: Money, memo: str = "") -> None:
        if not debit_account or not credit_account or debit_account == credit_account:
            raise ValueError("invalid accounting accounts")
        if amount.minor_units <= 0:
            raise ValueError("transaction amount must be positive")
        self.entries.extend((LedgerEntry(debit_account, amount, memo), LedgerEntry(credit_account, Money(-amount.minor_units, amount.currency), memo)))

    def balance(self, account: str, currency: str = "GEN") -> Money:
        return Money(sum(e.amount.minor_units for e in self.entries if e.account == account and e.amount.currency == currency), currency)

    def is_balanced(self, currency: str = "GEN") -> bool:
        return sum(e.amount.minor_units for e in self.entries if e.amount.currency == currency) == 0
