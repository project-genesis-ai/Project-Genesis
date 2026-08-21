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


def _planet_payload(simulation: Simulation) -> dict[str, Any]:
    snapshot = simulation.state.planet_snapshot
    if snapshot is None:
        return {"present": False}

    cells: list[dict[str, Any]] = []
    for row in snapshot.cells:
        for cell in row:
            cells.append(
                {
                    "x": cell.terrain.x,
                    "y": cell.terrain.y,
                    "elevation": round(cell.terrain.elevation_m, 6),
                    "land": cell.terrain.land,
                    "slope": round(cell.terrain.slope, 8),
                    "temperature": round(cell.atmosphere.temperature_c, 8),
                    "pressure": round(cell.atmosphere.pressure_kpa, 8),
                    "humidity": round(cell.atmosphere.humidity, 8),
                    "wind_u": round(cell.atmosphere.wind_u_mps, 8),
                    "wind_v": round(cell.atmosphere.wind_v_mps, 8),
                    "cloud": round(cell.atmosphere.cloud_cover, 8),
                    "precipitation": round(cell.atmosphere.precipitation_mm, 8),
                    "storm": round(cell.atmosphere.storm_intensity, 8),
                    "rainfall": round(cell.hydrology.rainfall_mm, 8),
                    "runoff": round(cell.hydrology.runoff_mm, 8),
                    "infiltration": round(cell.hydrology.infiltration_mm, 8),
                    "groundwater": round(cell.hydrology.groundwater_mm, 8),
                    "river_flow": round(cell.hydrology.river_flow, 8),
                    "lake_storage": round(cell.hydrology.lake_storage, 8),
                    "evaporation": round(cell.hydrology.evaporation_mm, 8),
                    "water_quality": round(cell.surface_water_quality, 8),
                    "pollution": round(cell.pollution, 8),
                    "biome": repr(cell.biome),
                }
            )

    routes = [
        {
            "x": route.x,
            "y": route.y,
            "downstream": [route.downstream_x, route.downstream_y],
            "path_length": route.path_length,
            "basin": route.basin_id,
            "terminal": route.terminal,
        }
        for route in snapshot.routes
    ]
    aquatic = [
        {"x": x, "y": y, "state": repr(cell)}
        for x, y, cell in sorted(snapshot.aquatic, key=lambda item: (item[1], item[0]))
    ]
    deep_ocean = [
        {"x": x, "y": y, "state": repr(cell)}
        for x, y, cell in sorted(snapshot.deep_ocean, key=lambda item: (item[1], item[0]))
    ]
    return {
        "present": True,
        "tick": snapshot.tick,
        "width": len(snapshot.cells[0]) if snapshot.cells else 0,
        "height": len(snapshot.cells),
        "cells": cells,
        "routes": routes,
        "aquatic": aquatic,
        "deep_ocean": deep_ocean,
    }


def build_checkpoint(simulation: Simulation) -> AuditCheckpoint:
    state = simulation.state
    payload: dict[str, Any] = {
        "tick": simulation.time.tick,
        "metrics": asdict(simulation.metrics()),
        "planet": _planet_payload(simulation),
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
