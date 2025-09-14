from __future__ import annotations

import threading
import time

import httpx

from aegis.api import app
import socket
def get_free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_compliance_report_steps_override_changes_epsilon(monkeypatch):
    import uvicorn

    class UvicornThread(threading.Thread):
        def __init__(self, port: int):
            super().__init__(daemon=True)
            self.server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))

        def run(self):
            self.server.run()

    monkeypatch.setenv("AEGIS_REQUIRE_MTLS_SIM", "0")

    port = get_free_port()
    t = UvicornThread(port)
    t.start()
    time.sleep(0.5)

    r1 = httpx.get(f"http://127.0.0.1:{port}/compliance/report", headers={"X-Role": "viewer"}, params={"steps": 1000}, timeout=5)
    r2 = httpx.get(f"http://127.0.0.1:{port}/compliance/report", headers={"X-Role": "viewer"}, params={"steps": 4000}, timeout=5)
    assert r1.status_code == 200 and r2.status_code == 200
    md1 = r1.json()["markdown"]
    md2 = r2.json()["markdown"]
    assert "Epsilon (approx., 1000 steps):" in md1
    assert "Epsilon (approx., 4000 steps):" in md2
    # Epsilon should increase with more steps (lower privacy), so strings should differ
    assert md1 != md2
