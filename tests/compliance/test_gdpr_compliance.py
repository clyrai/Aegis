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
def test_gdpr_compliance_endpoints():
    port = get_free_port()
    _start(port)
    base = f"http://127.0.0.1:{port}"

    # viewer cannot call GDPR
    r = httpx.post(f"{base}/compliance/gdpr", headers={"X-Role": "viewer"}, json={"action": "export", "subject_id": "abc"})
    assert r.status_code == 403

    # operator can call GDPR
    r = httpx.post(f"{base}/compliance/gdpr", headers={"X-Role": "operator"}, json={"action": "export", "subject_id": "abc"})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # invalid action rejected by validation
    r = httpx.post(f"{base}/compliance/gdpr", headers={"X-Role": "admin"}, json={"action": "erase", "subject_id": "abc"})
    assert r.status_code == 422
