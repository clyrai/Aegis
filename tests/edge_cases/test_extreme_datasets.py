from __future__ import annotations

import threading
import time

import httpx
import pytest

from aegis.api import app
from aegis.security.rbac import Role


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8014):
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


@pytest.mark.timeout(15)
def test_extreme_dataset_warnings():
    srv = ServerThread(app)
    srv.start()
    wait_for_server("http://127.0.0.1:8014/openapi.json")

    base = {
        "client_id": "c1",
        "num_samples": 50,
        "num_features": 15000,
        "missing_fraction": 0.2,
        "class_counts": {"maj": 990, "min": 10},
        "schema": ["f1", "f2"],
    }

    # First registration: expect warnings for tiny, high-dim, missing, high-missingness, class-imbalance
    r = httpx.post(
        "http://127.0.0.1:8014/dataset/register",
        headers={"X-Role": Role.admin.value},
        json=base,
    )
    assert r.status_code == 200, r.text
    warnings = r.json().get("warnings", [])
    joined = " ".join(warnings)
    assert "tiny-dataset" in joined
    assert "high-dimensional" in joined
    assert "missing-values" in joined
    assert "high-missingness" in joined
    assert "class-imbalance" in joined

    # Massive dataset scenario
    payload = {**base, "client_id": "c2", "num_samples": 2_000_000, "schema": ["f1", "f3"]}
    r = httpx.post(
        "http://127.0.0.1:8014/dataset/register",
        headers={"X-Role": Role.admin.value},
        json=payload,
    )
    assert r.status_code == 200, r.text
    warnings = r.json().get("warnings", [])
    joined = " ".join(warnings)
    assert "massive-dataset" in joined
    # schema mismatch vs first participant
    assert "schema-mismatch" in joined

