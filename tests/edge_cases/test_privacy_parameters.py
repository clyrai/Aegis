from __future__ import annotations

import threading
import time

import httpx
import pytest

from aegis.api import app
from aegis.security.rbac import Role


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8013):
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
def test_privacy_assessment_and_budget():
    srv = ServerThread(app)
    srv.start()
    wait_for_server("http://127.0.0.1:8013/openapi.json")

    # Configure DP
    r = httpx.post(
        "http://127.0.0.1:8013/dp/config",
        headers={"X-Role": Role.operator.value},
        json={
            "clipping_norm": 1.0,
            "noise_multiplier": 2.0,
            "sample_rate": 0.2,
            "delta": 1e-5,
            "accountant": "rdp",
        },
    )
    assert r.status_code == 200, r.text

    # Assess with low steps -> expect not ultra-low but may have high-sample-rate note
    r = httpx.get("http://127.0.0.1:8013/dp/assess", headers={"X-Role": Role.operator.value}, params={"steps": 10})
    assert r.status_code == 200
    js = r.json()
    assert "epsilon" in js and "delta" in js

    # Assess with very high steps -> high epsilon warning likely
    r = httpx.get(
        "http://127.0.0.1:8013/dp/assess",
        headers={"X-Role": Role.operator.value},
        params={"steps": 200000},
    )
    assert r.status_code == 200
    notes = r.json().get("notes", "")
    assert isinstance(notes, str)

    # Budget consume and reset
    r = httpx.post(
        "http://127.0.0.1:8013/dp/budget/consume",
        headers={"X-Role": Role.admin.value},
        params={"steps": 1000},
    )
    assert r.status_code == 200
    spent1 = r.json().get("spent_epsilon", 0.0)
    r = httpx.post(
        "http://127.0.0.1:8013/dp/budget/consume",
        headers={"X-Role": Role.admin.value},
        params={"steps": 1000},
    )
    spent2 = r.json().get("spent_epsilon", 0.0)
    assert spent2 >= spent1
    r = httpx.post("http://127.0.0.1:8013/dp/budget/reset", headers={"X-Role": Role.admin.value})
    assert r.status_code == 200
