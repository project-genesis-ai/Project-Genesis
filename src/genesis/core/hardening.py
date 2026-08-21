from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class HardeningReport:
    finite_state: bool
    non_negative_resources: bool
    non_negative_wallets: bool
    valid_health: bool
    balanced_ledger: bool = True
    bounded_governance: bool = True
    faults: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return all((
            self.finite_state,
            self.non_negative_resources,
            self.non_negative_wallets,
            self.valid_health,
            self.balanced_ledger,
            self.bounded_governance,
        ))


def _finite(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def audit_state(simulation) -> HardeningReport:
    """Audit authoritative state for production-safety invariants.

    This is deliberately read-only. It never repairs state silently, because a
    hidden mutation during an audit would make deterministic replay impossible.
    """
    faults: list[str] = []
    state = simulation.state

    finite = True
    for agent_id, agent in state.agents.items():
        if not all(_finite(value) for value in (agent.health, agent.wealth, agent.needs.hunger, agent.needs.thirst, agent.needs.energy, agent.needs.social, agent.needs.comfort)):
            finite = False
            faults.append(f"non-finite agent state: {agent_id}")
        for skill, value in agent.skills.items():
            if not _finite(value):
                finite = False
                faults.append(f"non-finite skill: {agent_id}:{skill}")

    for resource_id, value in state.resources.quantities.items():
        if not _finite(value):
            finite = False
            faults.append(f"non-finite resource: {resource_id}")

    for owner_id, wallet in state.wallets.items():
        if not _finite(wallet.balance):
            finite = False
            faults.append(f"non-finite wallet: {owner_id}")

    resources_ok = all(_finite(value) and float(value) >= 0.0 for value in state.resources.quantities.values())
    if not resources_ok:
        faults.append("resource quantity below zero")

    wallets_ok = all(_finite(wallet.balance) and wallet.balance >= 0.0 for wallet in state.wallets.values())
    if not wallets_ok:
        faults.append("wallet balance below zero")

    health_ok = all(_finite(agent.health) and 0.0 <= float(agent.health) <= 1.0 for agent in state.agents.values())
    if not health_ok:
        faults.append("agent health outside [0,1]")

    balanced_ledger = bool(state.ledger.is_balanced())
    if not balanced_ledger:
        faults.append("double-entry ledger is unbalanced")
    transaction_ids = [item.transaction_id for item in state.ledger.transactions]
    if len(transaction_ids) != len(set(transaction_ids)):
        balanced_ledger = False
        faults.append("duplicate ledger transaction id")

    bounded_governance = True
    for government_id, government in state.governments.items():
        if not _finite(government.treasury) or government.treasury < 0.0:
            bounded_governance = False
            faults.append(f"invalid government treasury: {government_id}")
        if not _finite(government.approval) or not 0.0 <= government.approval <= 1.0:
            bounded_governance = False
            faults.append(f"government approval outside [0,1]: {government_id}")
        if any(not _finite(value) or value < 0.0 for value in government.public_services.values()):
            bounded_governance = False
            faults.append(f"invalid public-service spending: {government_id}")

    return HardeningReport(
        finite_state=finite,
        non_negative_resources=resources_ok,
        non_negative_wallets=wallets_ok,
        valid_health=health_ok,
        balanced_ledger=balanced_ledger,
        bounded_governance=bounded_governance,
        faults=tuple(dict.fromkeys(faults)),
    )
