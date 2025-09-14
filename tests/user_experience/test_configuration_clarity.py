from __future__ import annotations

import threading
import time
import httpx
import uvicorn

from aegis.api import app


def _spawn(port: int) -> None:
    class T(threading.Thread):
        def __init__(self):
            super().__init__(daemon=True)
            self.server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
        def run(self):
            self.server.run()
    t = T()
    t.start()
    # wait
    for _ in range(100):
        try:
            httpx.get(f"http://127.0.0.1:{port}/openapi.json", timeout=0.25)
            break
        except Exception:
            time.sleep(0.05)


def test_dp_config_validation_and_messages():
    port = 8012
    _spawn(port)
    base = f"http://127.0.0.1:{port}"
    # invalid clipping norm (<=0)
    r = httpx.post(
        f"{base}/dp/config",
        headers={"X-Role": "operator"},
        json={"clipping_norm": 0, "noise_multiplier": 1.0, "sample_rate": 0.01, "delta": 1e-5, "accountant": "rdp"},
        timeout=1.0,
    )
    assert r.status_code == 422  # pydantic validation on Field(gt=0)

    # invalid sample_rate (>1)
    r = httpx.post(
        f"{base}/dp/config",
        headers={"X-Role": "operator"},
        json={"clipping_norm": 1.0, "noise_multiplier": 1.0, "sample_rate": 2.0, "delta": 1e-5, "accountant": "rdp"},
        timeout=1.0,
    )
    assert r.status_code == 422

    # valid config should pass
    r = httpx.post(
        f"{base}/dp/config",
        headers={"X-Role": "operator"},
        json={"clipping_norm": 1.0, "noise_multiplier": 1.0, "sample_rate": 0.01, "delta": 1e-5, "accountant": "rdp"},
        timeout=1.0,
    )
    assert r.status_code == 200
