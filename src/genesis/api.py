"""HTTP API for the deterministic Genesis runtime, persistence and 3D client."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from genesis.core.genesis_runtime import GenesisRuntime
from genesis.persistence.store import GenesisStore, database_url

_RUNTIME = GenesisRuntime()
_STORE: GenesisStore | None = None
_RUN_ID: str | None = None
_PERSIST_INTERVAL = 100
_WEB_ROOT = Path(__file__).resolve().parents[2] / "web"


def _initialize_runtime() -> None:
    global _STORE, _RUN_ID
    if database_url():
        _STORE = GenesisStore()
        _RUN_ID = _STORE.ensure_run(_RUNTIME)
        try:
            restored = _STORE.load_latest(_RUNTIME, _RUN_ID)
        except Exception:
            restored = False
        if not restored:
            _RUNTIME.simulation.state.initialize_planet()
            _STORE.save(_RUNTIME, _RUN_ID)
    else:
        _RUNTIME.simulation.state.initialize_planet()

_initialize_runtime()


def _jsonable(value):
    if is_dataclass(value):
        return {k: _jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if hasattr(value, "value") and isinstance(value.value, (str, int, float, bool, type(None))):
        return value.value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _planet_snapshot():
    snapshot = _RUNTIME.simulation.state.planet_snapshot
    if snapshot is None:
        _RUNTIME.simulation.state.initialize_planet()
        snapshot = _RUNTIME.simulation.state.planet_snapshot
    if snapshot is None:
        raise RuntimeError("planet snapshot failed to initialize")
    return _jsonable(snapshot)


def _visual_planet() -> dict:
    """Return a stable visualization DTO while preserving the raw snapshot API."""
    planet = _planet_snapshot()
    river_network = planet.get("rivers") or {}
    segments = river_network.get("segments", []) if isinstance(river_network, dict) else []
    planet["rivers"] = [
        {
            "x": segment.get("x"),
            "y": segment.get("y"),
            "downstream": [segment.get("downstream_x"), segment.get("downstream_y")],
            "discharge_mm": segment.get("discharge_mm", 0.0),
            "order": segment.get("order", 1),
            "basin_id": segment.get("basin_id"),
        }
        for segment in segments
        if segment.get("x") is not None and segment.get("y") is not None
    ]
    return planet


def _visual_wildlife(state) -> list[dict]:
    wildlife = []
    for organism in sorted(state.ecosystem.organisms.values(), key=lambda item: item.organism_id):
        position = organism.position
        wildlife.append({
            "id": organism.organism_id,
            "organism_id": organism.organism_id,
            "species_id": organism.species.species_id,
            "position": [float(position.x), float(position.z)],
            "age_ticks": organism.age_ticks,
            "energy": organism.energy,
            "health": organism.health,
            "alive": organism.alive,
        })
    return wildlife


def _visual_state() -> dict:
    simulation = _RUNTIME.simulation
    state = simulation.state
    settlements = []
    for settlement in sorted(state.civilization.settlements.values(), key=lambda item: item.settlement_id):
        settlements.append({
            "id": settlement.settlement_id,
            "name": settlement.name,
            "kind": _jsonable(settlement.kind),
            "location": list(settlement.location),
            "population": len(settlement.population),
            "residents": sorted(settlement.population),
            "stored_resources": _jsonable(settlement.stored_resources),
            "buildings": [
                {"id": building.building_id, "kind": _jsonable(building.kind), "capacity": building.capacity, "condition": building.condition, "occupants": sorted(building.occupants)}
                for building in sorted(settlement.buildings.values(), key=lambda item: item.building_id)
            ],
        })
    agents = []
    for agent in sorted(state.agents.values(), key=lambda item: item.agent_id):
        person = state.demography.people.get(agent.agent_id)
        agents.append({
            "id": agent.agent_id,
            "name": agent.name,
            "position": [agent.world_x, agent.world_y],
            "health": agent.health,
            "age_ticks": agent.age_ticks,
            "wealth": agent.wealth,
            "settlement_id": state.civilization.agent_settlements.get(agent.agent_id),
            "life_state": person.stage.value if person is not None else None,
        })
    events = [_jsonable(item) for item in state.history.all()[-100:]]
    return {
        "tick": simulation.time.tick,
        "metrics": _jsonable(simulation.metrics()),
        "planet": _visual_planet(),
        "agents": agents,
        "wildlife": _visual_wildlife(state),
        "settlements": settlements,
        "farms": [_jsonable(item) for item in sorted(state.civilization.farms.values(), key=lambda item: item.farm_id)],
        "resources": _jsonable(state.resources),
        "environment": _jsonable(state.environment),
        "events": events,
        "persistence": {"configured": _STORE is not None, "run_id": _RUN_ID},
    }


def _step(count: int) -> None:
    if count < 1 or count > 1000:
        raise ValueError("count must be between 1 and 1000")
    for _ in range(count):
        _RUNTIME.step()
        if _STORE is not None and _RUNTIME.simulation.time.tick % _PERSIST_INTERVAL == 0:
            _STORE.save(_RUNTIME, _RUN_ID)


class GenesisHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: object) -> None:
        body = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, path: Path) -> None:
        resolved = path.resolve()
        if not resolved.is_file() or _WEB_ROOT.resolve() not in resolved.parents:
            self._send_json(404, {"error": "not_found"})
            return
        content_type = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8"}.get(resolved.suffix, "application/octet-stream")
        body = resolved.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path == "/health":
            database = {"configured": _STORE is not None, "reachable": False}
            if _STORE is not None:
                try:
                    database["reachable"] = _STORE.ping()
                except Exception:
                    pass
            self._send_json(200, {"status": "ok", "service": "project-genesis", "database": database})
            return
        if path in {"/world/state", "/visualization"}:
            try:
                self._send_json(200, _visual_state())
            except Exception as exc:
                self._send_json(500, {"error": str(exc)})
            return
        if path in {"/world", "/snapshot", "/planet", "/genesis"}:
            try:
                self._send_json(200, {"tick": _RUNTIME.simulation.time.tick, "snapshot": _planet_snapshot()})
            except Exception as exc:
                self._send_json(500, {"error": str(exc)})
            return
        if path == "/metrics":
            try:
                self._send_json(200, _jsonable(_RUNTIME.simulation.metrics()))
            except Exception as exc:
                self._send_json(500, {"error": str(exc)})
            return
        if path == "/persistence":
            try:
                checkpoint = _STORE.latest_checkpoint(_RUN_ID) if _STORE is not None else None
                self._send_json(200, {"configured": _STORE is not None, "run_id": _RUN_ID, "latest_tick": checkpoint.tick if checkpoint else None, "digest": checkpoint.digest if checkpoint else None})
            except Exception as exc:
                self._send_json(500, {"error": str(exc)})
            return
        if path == "/":
            self._send_static(_WEB_ROOT / "index.html")
            return
        if path in {"/app.js", "/styles.css"}:
            self._send_static(_WEB_ROOT / path.lstrip("/"))
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "/step":
            try:
                count = int(parse_qs(parsed.query).get("count", ["1"])[0])
                _step(count)
                checkpoint = _STORE.latest_checkpoint(_RUN_ID) if _STORE is not None else None
                self._send_json(200, {"tick": _RUNTIME.simulation.time.tick, "checkpoint_tick": checkpoint.tick if checkpoint else None})
            except Exception as exc:
                self._send_json(500, {"error": str(exc)})
            return
        if path == "/checkpoint":
            try:
                if _STORE is None:
                    raise RuntimeError("DATABASE_URL is not configured")
                checkpoint = _STORE.save(_RUNTIME, _RUN_ID)
                self._send_json(200, {"tick": checkpoint.tick, "digest": checkpoint.digest})
            except Exception as exc:
                self._send_json(500, {"error": str(exc)})
            return
        self._send_json(404, {"error": "not_found"})

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=10000)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), GenesisHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if _STORE is not None:
            try:
                _STORE.save(_RUNTIME, _RUN_ID)
            except Exception:
                pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
