from __future__ import annotations

import threading
import time

import httpx

from aegis.api import app
from aegis.security.rbac import Role


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port: int = 8017):
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


def _mi_accuracy(n: int, sigma: float) -> float:
    import random

    random.seed(0)
    train = [random.gauss(0.4, sigma) for _ in range(n)]
    non = [random.gauss(0.6, sigma) for _ in range(n)]
    thr = 0.5
    tp = sum(1 for s in train if s < thr)
    tn = sum(1 for s in non if s >= thr)
    return (tp + tn) / (2 * n)


def _inversion_error(sigma: float, n: int = 1000) -> float:
    import random

    random.seed(1)
    true_mean = 0.7
    noise = random.gauss(0, sigma / max(n, 1))
    priv = true_mean + noise
    return abs(priv - true_mean)


def test_attack_resilience_tracks_noise_and_epsilon():
    port = 8017
    srv = ServerThread(app, port=port)
    srv.start()
    wait_for_server(f"http://127.0.0.1:{port}/openapi.json")

    steps = 10000
    # Low noise -> higher epsilon
    cfg_low = {"clipping_norm": 1.0, "noise_multiplier": 0.2, "sample_rate": 0.05, "delta": 1e-5, "accountant": "rdp"}
    r = httpx.post(f"http://127.0.0.1:{port}/dp/config", headers={"X-Role": Role.operator.value}, json=cfg_low)
    assert r.status_code == 200
    r = httpx.get(f"http://127.0.0.1:{port}/dp/assess", headers={"X-Role": Role.operator.value}, params={"steps": steps})
    eps_low = r.json()["epsilon"]

    # High noise -> lower epsilon
    cfg_high = {**cfg_low, "noise_multiplier": 2.0}
    r = httpx.post(f"http://127.0.0.1:{port}/dp/config", headers={"X-Role": Role.operator.value}, json=cfg_high)
    assert r.status_code == 200
    r = httpx.get(f"http://127.0.0.1:{port}/dp/assess", headers={"X-Role": Role.operator.value}, params={"steps": steps})
    eps_high = r.json()["epsilon"]

    assert eps_high < eps_low

    # Simulated MI accuracy decreases with higher sigma
    acc_low = _mi_accuracy(2000, sigma=cfg_low["noise_multiplier"])
    acc_high = _mi_accuracy(2000, sigma=cfg_high["noise_multiplier"])
    assert acc_high <= acc_low

    # Simulated inversion error increases with higher sigma
    err_low = _inversion_error(cfg_low["noise_multiplier"])
    err_high = _inversion_error(cfg_high["noise_multiplier"])
    assert err_high >= err_low
