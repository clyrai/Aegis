from __future__ import annotations

import threading
import time

import httpx
import pytest

from aegis.api import app
import socket
def get_free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8021):
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


def _start_session(i: int, port: int):
    base = f"http://127.0.0.1:{port}"
    httpx.post(f"{base}/participants", headers={"X-Role": "admin"}, json={"client_id": f"c{i}", "key_hex": "aa"})
    httpx.post(f"{base}/training/start", headers={"X-Role": "operator"}, json={"session_id": f"s{i}", "rounds": 1})


@pytest.mark.timeout(20)
def test_training_load_concurrent_sessions():
    port = get_free_port()
    srv = ServerThread(app, port=port)
    srv.start()
    wait_for_server(f"http://127.0.0.1:{port}/openapi.json")

    # Configure DP once
    httpx.post(
        f"http://127.0.0.1:{port}/dp/config",
        headers={"X-Role": "operator"},
        json={"clipping_norm": 1.0, "noise_multiplier": 1.0, "sample_rate": 0.01, "delta": 1e-5, "accountant": "rdp"},
    )

    threads = [threading.Thread(target=_start_session, args=(i, port)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Spot-check a few statuses
    ok = 0
    for i in range(10):
        r = httpx.get(f"http://127.0.0.1:{port}/training/status", headers={"X-Role": "viewer"}, params={"session_id": f"s{i}"})
        if r.status_code == 200:
            ok += 1
    assert ok >= 5
    # best-effort shutdown
    try:
        srv.server.should_exit = True  # type: ignore[attr-defined]
    except Exception:
        pass
