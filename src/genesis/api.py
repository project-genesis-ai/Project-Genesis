"""HTTP API for the deterministic Genesis runtime and 3D client."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from genesis.core.genesis_runtime import GenesisRuntime


_RUNTIME = GenesisRuntime()
_RUNTIME.simulation.state.initialize_planet()


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


class GenesisHandler(BaseHTTPRequestHandler):
    """Serve health and authoritative read-only world state."""

    def _send_json(self, status: int, payload: object) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path == "/health":
            self._send_json(200, {"status": "ok", "service": "project-genesis"})
            return
        if path in {"/world", "/snapshot", "/planet", "/genesis"}:
            try:
                self._send_json(200, {"snapshot": _planet_snapshot()})
            except Exception as exc:  # pragma: no cover
                self._send_json(500, {"error": str(exc)})
            return
        if path == "/metrics":
            try:
                self._send_json(200, _jsonable(_RUNTIME.simulation.metrics()))
            except Exception as exc:  # pragma: no cover
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
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
