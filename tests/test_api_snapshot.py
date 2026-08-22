from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from genesis.api import GenesisHandler, _planet_snapshot


def test_planet_snapshot_exposes_authoritative_cells() -> None:
    snapshot = _planet_snapshot()
    assert snapshot["tick"] == 0
    assert snapshot["cells"]
    assert snapshot["cells"][0]
    first = snapshot["cells"][0][0]
    assert {"terrain", "atmosphere", "hydrology", "biome"} <= set(first)
    assert {"x", "y", "elevation_m", "land", "slope"} <= set(first["terrain"])


def test_http_world_endpoint_returns_snapshot(monkeypatch) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), GenesisHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        conn = HTTPConnection(host, port, timeout=10)
        conn.request("GET", "/world")
        response = conn.getresponse()
        payload = json.loads(response.read())
        assert response.status == 200
        assert "snapshot" in payload
        assert payload["snapshot"]["tick"] == 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
