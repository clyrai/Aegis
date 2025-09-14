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
def test_hipaa_summary_and_rbac():
    port = get_free_port()
    _start(port)
    base = f"http://127.0.0.1:{port}"

    # viewer cannot access HIPAA summary
    r = httpx.get(f"{base}/compliance/hipaa", headers={"X-Role": "viewer"})
    assert r.status_code == 403

    # admin allowed
    r = httpx.get(f"{base}/compliance/hipaa", headers={"X-Role": "admin"})
    assert r.status_code == 200
    data = r.json()
    assert data["phi_at_rest"] is False
    assert data["phi_in_transit_protected"] is True
