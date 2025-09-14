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


def test_compliance_report_markdown_contains_epsilon_and_versions(monkeypatch):
    import uvicorn

    class UvicornThread(threading.Thread):
        def __init__(self):
            super().__init__(daemon=True)
            self.server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))

        def run(self):
            self.server.run()

    monkeypatch.setenv("AEGIS_REQUIRE_MTLS_SIM", "0")

    port = get_free_port()
    t = UvicornThread()
    t.start()
    time.sleep(0.5)

    r = httpx.get(f"http://127.0.0.1:{port}/compliance/report", headers={"X-Role": "viewer"}, timeout=5)
    assert r.status_code == 200
    md = r.json()["markdown"]
    assert "Epsilon (approx." in md
    assert "## Versions" in md
