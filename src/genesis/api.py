"""HTTP API for the deterministic Genesis runtime and durable persistence."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from genesis.core.genesis_runtime import GenesisRuntime
from genesis.persistence.store import GenesisStore, PersistenceError, database_url


_RUNTIME = GenesisRuntime()
_STORE: GenesisStore | None = None
_RUN_ID: str | None = None
_PERSIST_INTERVAL = 100


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
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
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


def _step(count: int) -> None:
    if count < 1 or count > 1000:
        raise ValueError("count must be between 1 and 1000")
    for _ in range(count):
        _RUNTIME.step()
        if _STORE is not None and _RUNTIME.simulation.time.tick % _PERSIST_INTERVAL == 0:
            _STORE.save(_RUNTIME, _RUN_ID)


class GenesisHandler(BaseHTTPRequestHandler):
    """Serve health, authoritative world state and controlled simulation stepping."""

    def _send_json(self, status: int, payload: object) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
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
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") == "/step":
            try:
                count = int(parse_qs(parsed.query).get("count", ["1"])[0])
                _step(count)
                if _STORE is not None and _RUNTIME.simulation.time.tick % _PERSIST_INTERVAL != 0:
                    _STORE.save(_RUNTIME, _RUN_ID)
                self._send_json(200, {"tick": _RUNTIME.simulation.time.tick, "persisted": _STORE is not None})
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
