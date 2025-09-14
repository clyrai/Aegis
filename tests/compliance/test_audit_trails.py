import threading
import time

import httpx
import pytest
import socket


def get_free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _start(port: int):
    import uvicorn
    from aegis.api import app

    class S(threading.Thread):
        def __init__(self):
            super().__init__(daemon=True)
            self.server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))

        def run(self):
            self.server.run()

    t = S()
    t.start()
    for _ in range(40):
        try:
            httpx.get(f"http://127.0.0.1:{port}/openapi.json").raise_for_status()
            return
        except Exception:
            time.sleep(0.05)


@pytest.mark.timeout(15)
def test_audit_log_contains_events_and_chain_is_valid():
    port = get_free_port()
    _start(port)
    base = f"http://127.0.0.1:{port}"

    # Generate a few events
    httpx.post(f"{base}/participants", headers={"X-Role": "admin"}, json={"client_id": "c1", "key_hex": "aa"}).raise_for_status()
    httpx.post(f"{base}/dp/config", headers={"X-Role": "admin"}, json={"clipping_norm": 1.0, "noise_multiplier": 1.0, "sample_rate": 0.1, "delta": 1e-5, "accountant": "rdp"}).raise_for_status()
    httpx.get(f"{base}/compliance/report", headers={"X-Role": "viewer", "X-Client-Cert": "1"}).raise_for_status()

    # Audit log read requires viewer/admin
    r = httpx.get(f"{base}/audit/logs", headers={"X-Role": "viewer"})
    assert r.status_code == 200
    data = r.json()
    assert data["valid_chain"] is True
    assert len(data["events"]) >= 3
