from __future__ import annotations

import threading
import time

import httpx

from aegis.api import app


def test_mtls_sim_enforced(monkeypatch):
    import uvicorn

    class UvicornThread(threading.Thread):
        def __init__(self):
            super().__init__(daemon=True)
            self.server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8006, log_level="warning"))

        def run(self):
            self.server.run()

    # Enable simulated mTLS requirement
    monkeypatch.setenv("AEGIS_REQUIRE_MTLS_SIM", "1")

    t = UvicornThread()
    t.start()
    time.sleep(0.5)

    # Missing client cert header should be forbidden
    r = httpx.get("http://127.0.0.1:8006/compliance/report", headers={"X-Role": "viewer"}, timeout=5)
    assert r.status_code == 403

    # Presenting the header allows access
    r2 = httpx.get("http://127.0.0.1:8006/compliance/report", headers={"X-Role": "viewer", "X-Client-Cert": "dummy"}, timeout=5)
    assert r2.status_code == 200
