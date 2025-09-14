from __future__ import annotations

import httpx
import threading
import time

from aegis.api import app
from aegis.security.rbac import Role


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8001):
        super().__init__(daemon=True)
        import uvicorn
        self.config = uvicorn.Config(app, host=host, port=port, log_level="warning")
        self.server = uvicorn.Server(self.config)

    def run(self):
        self.server.run()


def wait_for_server(url: str, timeout: float = 5.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = httpx.get(url)
            if r.status_code in (200, 404):
                return
        except Exception:
            time.sleep(0.05)
    raise RuntimeError("server did not start")


def test_openapi_and_rbac_flow():
    # spin a lightweight dev server in thread
    srv = ServerThread(app)
    srv.start()
    wait_for_server("http://127.0.0.1:8001/openapi.json")

    # OpenAPI available
    r = httpx.get("http://127.0.0.1:8001/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert "paths" in spec

    # Viewer cannot register participant
    r = httpx.post(
        "http://127.0.0.1:8001/participants",
        headers={"X-Role": Role.viewer.value},
        json={"client_id": "c1", "key_hex": "6b31"},
    )
    assert r.status_code == 403

    # Admin registers participant
    r = httpx.post(
        "http://127.0.0.1:8001/participants",
        headers={"X-Role": Role.admin.value},
        json={"client_id": "c1", "key_hex": "6b31"},
    )
    assert r.status_code == 200
    assert "audit" in r.json()

    # Operator sets DP config with invalid values rejected
    r = httpx.post(
        "http://127.0.0.1:8001/dp/config",
        headers={"X-Role": Role.operator.value},
        json={"clipping_norm": -1, "noise_multiplier": 1.0, "sample_rate": 0.01, "delta": 1e-5, "accountant": "rdp"},
    )
    assert r.status_code == 422

    # Valid DP config
    r = httpx.post(
        "http://127.0.0.1:8001/dp/config",
        headers={"X-Role": Role.operator.value},
        json={"clipping_norm": 1.0, "noise_multiplier": 1.0, "sample_rate": 0.01, "delta": 1e-5, "accountant": "rdp"},
    )
    assert r.status_code == 200

    # Strategy selection
    r = httpx.post(
        "http://127.0.0.1:8001/strategy",
        headers={"X-Role": Role.operator.value},
        json={"strategy": "krum"},
    )
    assert r.status_code == 200

    # Start training requires operator/admin
    r = httpx.post(
        "http://127.0.0.1:8001/training/start",
        headers={"X-Role": Role.viewer.value},
        json={"session_id": "s1", "rounds": 1},
    )
    assert r.status_code == 403

    r = httpx.post(
        "http://127.0.0.1:8001/training/start",
        headers={"X-Role": Role.operator.value},
        json={"session_id": "s1", "rounds": 1},
    )
    assert r.status_code == 200

    # Status allowed for viewer
    r = httpx.get("http://127.0.0.1:8001/training/status", headers={"X-Role": Role.viewer.value}, params={"session_id": "s1"})
    assert r.status_code == 200
    assert r.json()["status"] in {"running", "stopped"}

    # Stop allowed for operator
    r = httpx.post("http://127.0.0.1:8001/training/stop", headers={"X-Role": Role.operator.value}, params={"session_id": "s1"})
    assert r.status_code == 200

    # Rate limit check on report generation (30/min). We'll hammer quickly a few times.
    for _ in range(5):
        r = httpx.get("http://127.0.0.1:8001/compliance/report", headers={"X-Role": Role.viewer.value})
        assert r.status_code == 200
