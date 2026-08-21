from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from genesis.civilization.government import Government
from genesis.economy.wallet import Wallet


@dataclass(frozen=True, slots=True)
class GovernanceEvent:
    government_id: str
    kind: str
    amount: float = 0.0
    subject_id: str | None = None


@dataclass(slots=True)
class GovernanceRuntime:
    """Deterministic bridge between canonical citizens, wallets and governments.

    Government remains the public-policy authority and SimulationState.wallets remains
    the private-balance authority. Binding replaces the runtime's registries with
    those canonical mappings, preventing a second economic state from emerging.
    """

    governments: dict[str, Government] = field(default_factory=dict)
    wallets: dict[str, Wallet] = field(default_factory=dict)
    tax_rate: float = 0.10
    service_budget_ratio: float = 0.50
    last_events: tuple[GovernanceEvent, ...] = ()
    bound: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.tax_rate <= 1.0:
            raise ValueError("tax_rate must be between 0 and 1")
        if not 0.0 <= self.service_budget_ratio <= 1.0:
            raise ValueError("service_budget_ratio must be between 0 and 1")

    def bind(self, governments: dict[str, Government], wallets: dict[str, Wallet]) -> None:
        if governments is None or wallets is None:
            raise ValueError("canonical government and wallet mappings are required")
        self.governments = governments
        self.wallets = wallets
        self.bound = True

    def add_government(self, government: Government) -> None:
        if government.government_id in self.governments:
            raise ValueError(f"government already exists: {government.government_id}")
        self.governments[government.government_id] = government

    def ensure_wallet(self, owner_id: str, balance: float = 0.0) -> Wallet:
        if owner_id in self.wallets:
            return self.wallets[owner_id]
        wallet = Wallet(owner_id, balance)
        self.wallets[owner_id] = wallet
        return wallet

    def register_citizen(self, government_id: str, citizen_id: str, balance: float = 0.0) -> None:
        government = self.governments.get(government_id)
        if government is None:
            raise ValueError(f"unknown government: {government_id}")
        government.add_citizen(citizen_id)
        self.ensure_wallet(citizen_id, balance)

    def collect_taxes(self, government_id: str, taxable_income: dict[str, float]) -> float:
        government = self.governments.get(government_id)
        if government is None:
            raise ValueError(f"unknown government: {government_id}")
        events: list[GovernanceEvent] = []
        collected = 0.0
        for citizen_id in sorted(government.population):
            income = taxable_income.get(citizen_id, 0.0)
            if income < 0.0:
                raise ValueError("taxable income cannot be negative")
            wallet = self.wallets.get(citizen_id)
            if wallet is None:
                continue
            tax = min(wallet.balance, income * self.tax_rate)
            if tax <= 0.0:
                continue
            if wallet.debit(tax):
                government.collect_tax(tax)
                collected += tax
                events.append(GovernanceEvent(government_id, "tax", tax, citizen_id))
        self.last_events = tuple(events)
        return collected

    def fund_services(self, government_id: str, service: str, amount: float) -> bool:
        government = self.governments.get(government_id)
        if government is None:
            raise ValueError(f"unknown government: {government_id}")
        if amount < 0.0:
            raise ValueError("service amount cannot be negative")
        max_budget = government.treasury * self.service_budget_ratio
        if amount > max_budget:
            return False
        if not government.spend(service, amount):
            return False
        self.last_events = (GovernanceEvent(government_id, "service", amount, service),)
        return True

    def transfer(self, sender_id: str, recipient_id: str, amount: float) -> bool:
        if sender_id == recipient_id:
            return False
        sender = self.wallets.get(sender_id)
        recipient = self.wallets.get(recipient_id)
        if sender is None or recipient is None:
            raise ValueError("both wallets must exist")
        if amount < 0.0:
            raise ValueError("transfer amount cannot be negative")
        return sender.transfer_to(recipient, amount)

    def money_supply(self) -> float:
        return sum(wallet.balance for wallet in self.wallets.values()) + sum(gov.treasury for gov in self.governments.values())

    def reconcile(self, before: float, tolerance: float = 1e-9) -> bool:
        if tolerance < 0.0:
            raise ValueError("tolerance cannot be negative")
        return abs(self.money_supply() - before) <= tolerance

    def tick(self, government_ids: Iterable[str] | None = None) -> None:
        selected = sorted(government_ids if government_ids is not None else self.governments)
        for government_id in selected:
            government = self.governments.get(government_id)
            if government is None:
                raise ValueError(f"unknown government: {government_id}")
            government.tick()
