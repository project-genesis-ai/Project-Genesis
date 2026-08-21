from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class HardeningReport:
    finite_state: bool
    non_negative_resources: bool
    non_negative_wallets: bool
    valid_health: bool


def audit_state(simulation) -> HardeningReport:
    finite = True
    for agent in simulation.state.agents.values():
        finite &= all(math.isfinite(float(v)) for v in (agent.health, agent.wealth))
    for value in simulation.state.resources.quantities.values():
        finite &= math.isfinite(float(value))
    for wallet in simulation.state.wallets.values():
        finite &= math.isfinite(float(wallet.balance))
    resources_ok = all(float(v) >= 0.0 for v in simulation.state.resources.quantities.values())
    wallets_ok = all(float(w.balance) >= 0.0 for w in simulation.state.wallets.values())
    health_ok = all(0.0 <= float(a.health) <= 1.0 for a in simulation.state.agents.values())
    return HardeningReport(finite, resources_ok, wallets_ok, health_ok)
