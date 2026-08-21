from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from genesis.core.simulation import Simulation


@dataclass(frozen=True, slots=True)
class AuditCheckpoint:
    tick: int
    digest: str
    payload: dict[str, Any]


def _object_type(value: Any) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


def _canonical(value: Any) -> Any:
    """Convert authoritative state into deterministic JSON-safe primitives."""
    if isinstance(value, Enum):
        return _canonical(value.value)
    if is_dataclass(value):
        return {field.name: _canonical(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        items = [(_canonical(key), _canonical(item)) for key, item in value.items()]
        items.sort(key=lambda item: json.dumps(item[0], sort_keys=True, separators=(",", ":"), default=str))
        return {str(key): item for key, item in items}
    if isinstance(value, (set, frozenset)):
        items = [_canonical(item) for item in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":"), default=str))
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("checkpoint cannot serialize non-finite float")
        return round(value, 12)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if hasattr(value, "__dict__"):
        return {"__type__": _object_type(value), "state": _canonical(vars(value))}
    slots = getattr(type(value), "__slots__", ())
    if isinstance(slots, str):
        slots = (slots,)
    if slots:
        state = {slot: _canonical(getattr(value, slot)) for slot in slots if slot not in {"__dict__", "__weakref__"} and hasattr(value, slot)}
        return {"__type__": _object_type(value), "state": state}
    return {"__type__": _object_type(value)}


def _planet_payload(simulation: Simulation) -> dict[str, Any]:
    snapshot = simulation.state.planet_snapshot
    if snapshot is None:
        return {"present": False}
    cells: list[dict[str, Any]] = []
    for row in snapshot.cells:
        for cell in row:
            cells.append({"x": cell.terrain.x, "y": cell.terrain.y, "elevation": cell.terrain.elevation_m, "land": cell.terrain.land, "slope": cell.terrain.slope, "atmosphere": cell.atmosphere, "hydrology": cell.hydrology, "biome": cell.biome, "water_quality": cell.surface_water_quality, "pollution": cell.pollution})
    routes = [{"x": route.x, "y": route.y, "downstream": [route.downstream_x, route.downstream_y], "path_length": route.path_length, "basin": route.basin_id, "terminal": route.terminal} for route in snapshot.routes]
    rivers = [{"x": segment.x, "y": segment.y, "downstream": [segment.downstream_x, segment.downstream_y], "discharge": segment.discharge_mm, "order": segment.order, "basin": segment.basin_id} for segment in snapshot.rivers.segments]
    return {"present": True, "tick": snapshot.tick, "width": len(snapshot.cells[0]) if snapshot.cells else 0, "height": len(snapshot.cells), "cells": cells, "routes": routes, "rivers": rivers, "lake_sinks": list(snapshot.rivers.lake_sinks), "aquatic": [{"x": x, "y": y, "state": cell} for x, y, cell in sorted(snapshot.aquatic, key=lambda item: (item[1], item[0]))], "deep_ocean": [{"x": x, "y": y, "state": cell} for x, y, cell in sorted(snapshot.deep_ocean, key=lambda item: (item[1], item[0]))], "topology": snapshot.topology}


def _life_payload(simulation: Simulation) -> dict[str, Any]:
    ecosystem = simulation.state.ecosystem
    return {"seed": ecosystem.seed, "next_birth_id": ecosystem._next_birth_id, "species": [item for item in sorted(ecosystem.species.values(), key=lambda value: value.species_id)], "organisms": [item for item in sorted(ecosystem.organisms.values(), key=lambda value: value.organism_id)]}


def _agents_payload(simulation: Simulation) -> list[dict[str, Any]]:
    state = simulation.state
    return [{"id": agent.agent_id, "name": agent.name, "age": agent.age_ticks, "health": agent.health, "needs": agent.needs, "personality": agent.personality, "inventory": agent.inventory, "wealth": agent.wealth, "skills": agent.skills, "knowledge": agent.knowledge, "memory": agent.memory, "position": [agent.world_x, agent.world_y]} for agent in sorted(state.agents.values(), key=lambda item: item.agent_id)]


def build_checkpoint(simulation: Simulation) -> AuditCheckpoint:
    state = simulation.state
    payload: dict[str, Any] = {"tick": simulation.time.tick, "metrics": asdict(simulation.metrics()), "world": state.world, "environment": state.environment, "physics": state.physics, "planet": _planet_payload(simulation), "life": _life_payload(simulation), "resources": state.resources, "utilities": state.utilities, "agents": _agents_payload(simulation), "health": state.health, "disasters": state.disasters, "transport": state.transport, "demography": state.demography, "labor": state.labor, "wallets": state.wallets, "ledger": state.ledger, "education": state.education, "learning_assistant": state.learning_assistant, "governments": state.governments, "politics": state.politics, "technologies": state.technologies, "innovation": state.innovation, "research": state.research, "social": state.social, "culture": state.culture, "cognition": state.cognition, "knowledge": state.knowledge, "civilization": state.civilization, "autonomy": state.autonomy, "planet_ecology": state.planet_ecology, "exploration": state.exploration, "exploration_discoveries": state.exploration_discoveries, "trading_company": state.trading_company, "events": state.history.all()}
    payload = _canonical(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return AuditCheckpoint(simulation.time.tick, digest, payload)
