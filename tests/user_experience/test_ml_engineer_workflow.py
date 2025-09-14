from __future__ import annotations

import threading
import time
import httpx
import uvicorn

from aegis.api import app


def _start_api(port: int) -> threading.Thread:
    class UThread(threading.Thread):
        def __init__(self):
            super().__init__(daemon=True)
            self.server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
        def run(self):
            self.server.run()
    t = UThread()
    t.start()
    # wait for server
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            httpx.get(f"{base}/openapi.json", timeout=0.25)
            break
        except Exception:
            time.sleep(0.05)
    return t


def test_ml_engineer_can_run_end_to_end_workflow():
    port = 8011
    _start_api(port)
    base = f"http://127.0.0.1:{port}"

    # Health and OpenAPI
    r = httpx.get(f"{base}/healthz")
    assert r.status_code == 200
    r = httpx.get(f"{base}/openapi.json")
    assert r.status_code == 200

    # Register 3 participants
    for i in range(1, 3 + 1):
        rr = httpx.post(
            f"{base}/participants",
            headers={"X-Role": "admin"},
            json={"client_id": f"c{i}", "key_hex": f"6b{i:02x}"},
            timeout=1.0,
        )
        assert rr.status_code == 200

    # Configure DP and strategy
    rr = httpx.post(
        f"{base}/dp/config",
        headers={"X-Role": "operator"},
        json={
            "clipping_norm": 1.0,
            "noise_multiplier": 1.0,
            "sample_rate": 0.01,
            "delta": 1e-5,
            "accountant": "rdp",
        },
        timeout=1.0,
    )
    assert rr.status_code == 200
    rr = httpx.post(
        f"{base}/strategy",
        headers={"X-Role": "operator"},
        json={"strategy": "trimmed_mean"},
        timeout=1.0,
    )
    assert rr.status_code == 200

    # Start, check status, stop
    rr = httpx.post(
        f"{base}/training/start",
        headers={"X-Role": "operator"},
        json={"session_id": "uxtest", "rounds": 3},
        timeout=1.0,
    )
    assert rr.status_code == 200
    rr = httpx.get(f"{base}/training/status", headers={"X-Role": "viewer"}, params={"session_id": "uxtest"}, timeout=1.0)
    assert rr.status_code == 200 and rr.json().get("status") == "running"
    rr = httpx.post(f"{base}/training/stop", headers={"X-Role": "operator"}, params={"session_id": "uxtest"}, timeout=1.0)
    assert rr.status_code == 200 and rr.json().get("status") == "stopped"

    # Report should be readable for non-technical user (basic check for title)
    rr = httpx.get(f"{base}/compliance/report", headers={"X-Role": "viewer"}, timeout=2.0)
    assert rr.status_code == 200
    md = rr.json().get("markdown", "")
    assert "Aegis Compliance Report" in md
