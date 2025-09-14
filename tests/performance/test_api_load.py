from __future__ import annotations

import socket
import threading
import time

import httpx
import pytest

from aegis.api import app
from aegis.security.rbac import Role

def get_free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8020):
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


@pytest.mark.timeout(20)
def test_api_load_basic_throughput():
    port = get_free_port()
    srv = ServerThread(app, port=port)
    srv.start()
    wait_for_server(f"http://127.0.0.1:{port}/openapi.json")

    # Warmup
    httpx.get(f"http://127.0.0.1:{port}/healthz")

    # Burst 100 requests to report; expect mostly 200 with some 429s possible due to rate limit
    successes = 0
    for _ in range(100):
        r = httpx.get(f"http://127.0.0.1:{port}/compliance/report", headers={"X-Role": Role.viewer.value})
        if r.status_code == 200:
            successes += 1
    assert successes >= 10
    try:
        srv.server.should_exit = True  # type: ignore[attr-defined]
    except Exception:
        pass
