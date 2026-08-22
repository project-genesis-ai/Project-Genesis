from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from genesis.api import GenesisHandler


def test_world_state_endpoint_exposes_authoritative_visual_data() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), GenesisHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        conn = HTTPConnection(host, port, timeout=10)
        conn.request("GET", "/world/state")
        response = conn.getresponse()
        payload = json.loads(response.read())
        assert response.status == 200
        assert {"tick", "metrics", "planet", "agents", "wildlife", "settlements", "farms", "resources", "environment", "events", "persistence"} <= set(payload)
        assert payload["planet"]["present"] is True
        assert payload["planet"]["cells"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
