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


def test_compliance_report_pdf(monkeypatch):
    import uvicorn

    class UvicornThread(threading.Thread):
        def __init__(self):
            super().__init__(daemon=True)
            self.server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))

        def run(self):
            self.server.run()

    # Ensure mTLS sim disabled for this test
    monkeypatch.setenv("AEGIS_REQUIRE_MTLS_SIM", "0")

    port = get_free_port()
    t = UvicornThread()
    t.start()
    time.sleep(0.5)

    # Request PDF
    r = httpx.get(f"http://127.0.0.1:{port}/compliance/report", params={"format": "pdf"}, headers={"X-Role": "viewer"}, timeout=5)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/pdf")
    assert len(r.content) > 100  # some bytes
