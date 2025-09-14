import os
import threading
import time

import httpx
import pytest


def get_free_port() -> int:
    import socket
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
def test_audit_checksum_changes_when_events_added(tmp_path):
    # enable file-backed audit to ensure no crash
    os.environ["AEGIS_AUDIT_LOG_FILE"] = str(tmp_path / "audit.jsonl")
    port = get_free_port()
    _start(port)
    base = f"http://127.0.0.1:{port}"

    # initial
    r0 = httpx.get(f"{base}/audit/checksum", headers={"X-Role": "viewer"})
    assert r0.status_code == 200
    c0 = r0.json()["checksum"]

    # add event
    httpx.post(f"{base}/participants", headers={"X-Role": "admin"}, json={"client_id": "c1", "key_hex": "aa"}).raise_for_status()

    r1 = httpx.get(f"{base}/audit/checksum", headers={"X-Role": "viewer"})
    assert r1.status_code == 200
    c1 = r1.json()["checksum"]
    assert c0 != c1
