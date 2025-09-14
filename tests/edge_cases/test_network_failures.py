from __future__ import annotations

import threading
import time
from typing import List

import httpx
import pytest

from aegis.api import app
from aegis.federated_coordinator import FederatedCoordinator, UpdateEnvelope
from aegis.security.rbac import Role


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port: int = 8015):
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


def test_intermittent_connectivity_aggregation():
    # Two valid clients, one invalid (dropped or bad signature)
    keys = {"c1": bytes.fromhex("aa"), "c2": bytes.fromhex("bb")}
    coord = FederatedCoordinator(aggregator="trimmed_mean", auth_keys=keys)
    u1 = UpdateEnvelope.sign("c1", 1, [1.0, 3.0], keys["c1"])
    u2 = UpdateEnvelope.sign("c2", 1, [3.0, 7.0], keys["c2"])
    # invalid: unknown client id
    bad = UpdateEnvelope.sign("cX", 1, [100.0, 100.0], b"00")
    out = coord.aggregate([u1, u2, bad])
    # Expect average of valid updates: [2.0, 5.0]
    assert out == pytest.approx([2.0, 5.0])


def test_certificate_expiration_simulated_mtls_enforcement(monkeypatch):
    # Enable simulated mTLS enforcement and assert missing client cert is rejected
    monkeypatch.setenv("AEGIS_REQUIRE_MTLS_SIM", "1")
    port = 8015
    srv = ServerThread(app, port=port)
    srv.start()
    wait_for_server(f"http://127.0.0.1:{port}/openapi.json")

    r = httpx.get(f"http://127.0.0.1:{port}/compliance/report", headers={"X-Role": Role.viewer.value})
    assert r.status_code == 403

    # With client cert header present, should pass
    r = httpx.get(
        f"http://127.0.0.1:{port}/compliance/report",
        headers={"X-Role": Role.viewer.value, "X-Client-Cert": "dummy-cert"},
    )
    assert r.status_code == 200


def test_bandwidth_limitation_rate_limiting():
    # Use a separate port to avoid conflicts
    port = 8016
    srv = ServerThread(app, port=port)
    srv.start()
    wait_for_server(f"http://127.0.0.1:{port}/openapi.json")

    # Hammer the report endpoint until we see 429 based on built-in limiter (30/min)
    statuses: List[int] = []
    for _ in range(40):
        r = httpx.get(f"http://127.0.0.1:{port}/compliance/report", headers={"X-Role": Role.viewer.value})
        statuses.append(r.status_code)
        if r.status_code == 429:
            break
    assert 429 in statuses
