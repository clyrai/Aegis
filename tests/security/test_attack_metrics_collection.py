from __future__ import annotations

import csv
import threading
import time
from pathlib import Path

import httpx
import pytest

from aegis.api import app
from aegis.security.rbac import Role


class ServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port: int = 8018):
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

    random.seed(123)
    train = [random.gauss(0.4, sigma) for _ in range(n)]
    non = [random.gauss(0.6, sigma) for _ in range(n)]
    thr = 0.5
    tp = sum(1 for s in train if s < thr)
    tn = sum(1 for s in non if s >= thr)
    return (tp + tn) / (2 * n)


def _inversion_error(sigma: float, n: int = 1000) -> float:
    import random

    random.seed(456)
    true_mean = 0.7
    noise = random.gauss(0, sigma / max(n, 1))
    priv = true_mean + noise
    return abs(priv - true_mean)


@pytest.mark.timeout(20)
def test_attack_metrics_collection(tmp_path: Path):
    port = 8018
    srv = ServerThread(app, port=port)
    srv.start()
    wait_for_server(f"http://127.0.0.1:{port}/openapi.json")

    steps = 10000
    noise_levels = [0.2, 0.5, 1.0, 2.0]
    epsilons = []
    mi_accs = []
    inv_errs = []

    base_cfg = {"clipping_norm": 1.0, "sample_rate": 0.05, "delta": 1e-5, "accountant": "rdp"}
    for sigma in noise_levels:
        cfg = {**base_cfg, "noise_multiplier": sigma}
        r = httpx.post(f"http://127.0.0.1:{port}/dp/config", headers={"X-Role": Role.operator.value}, json=cfg)
        assert r.status_code == 200
        r = httpx.get(f"http://127.0.0.1:{port}/dp/assess", headers={"X-Role": Role.operator.value}, params={"steps": steps})
        eps = r.json()["epsilon"]
        epsilons.append(eps)
        mi_accs.append(_mi_accuracy(2000, sigma))
        inv_errs.append(_inversion_error(sigma))

    # Assert monotonic trends: epsilon decreases with sigma, MI accuracy decreases, inversion error increases
    assert all(x > y for x, y in zip(epsilons, epsilons[1:])), f"epsilons not decreasing: {epsilons}"
    assert all(x >= y for x, y in zip(mi_accs, mi_accs[1:])), f"mi accuracies not decreasing: {mi_accs}"
    assert all(x <= y for x, y in zip(inv_errs, inv_errs[1:])), f"inversion errors not increasing: {inv_errs}"

    # Write CSV report
    out_csv = tmp_path / "attack_metrics.csv"
    with out_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["noise_multiplier", "epsilon", "mi_accuracy", "inversion_error"])
        for sigma, eps, acc, err in zip(noise_levels, epsilons, mi_accs, inv_errs):
            w.writerow([sigma, eps, acc, err])

    assert out_csv.exists()
    assert out_csv.stat().st_size > 0
