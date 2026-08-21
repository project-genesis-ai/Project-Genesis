from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from genesis.core.simulation import Simulation


@dataclass(frozen=True, slots=True)
class AuditCheckpoint:
    tick: int
    digest: str
    payload: dict[str, Any]


def build_checkpoint(simulation: Simulation) -> AuditCheckpoint:
    state = simulation.state
    payload: dict[str, Any] = {
        "tick": simulation.time.tick,
        "metrics": asdict(simulation.metrics()),
        "agents": [
            {
                "id": agent.agent_id,
                "age": agent.age_ticks,
                "health": round(agent.health, 12),
                "wealth": round(agent.wealth, 12),
                "position": [agent.world_x, agent.world_y],
                "skills": {key: round(value, 12) for key, value in sorted(agent.skills.items())},
                "knowledge": sorted(agent.knowledge),
            }
            for agent in sorted(state.agents.values(), key=lambda item: item.agent_id)
        ],
        "settlements": [
            {
                "id": settlement.settlement_id,
                "kind": settlement.kind.value,
                "population": sorted(settlement.population),
                "location": list(settlement.location),
            }
            for settlement in sorted(state.civilization.settlements.values(), key=lambda item: item.settlement_id)
        ],
        "technologies": {
            key: {"progress": round(value.progress, 12), "unlocked": value.unlocked}
            for key, value in sorted(state.technologies.items())
        },
        "innovations": sorted(state.innovation.discovered),
        "ledger_balances": {key: round(value, 12) for key, value in sorted(state.ledger.balances.items())},
        "events": [
            {"tick": event.tick, "type": event.event_type, "actor": event.actor_id, "target": event.target_id, "data": event.data}
            for event in state.history.all()
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return AuditCheckpoint(simulation.time.tick, digest, payload)
