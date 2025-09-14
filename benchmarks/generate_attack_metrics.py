from __future__ import annotations

import csv
import threading
import time
from pathlib import Path

import httpx


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


def _start_api(port: int):
    import uvicorn
    from aegis.api import app

    class UThread(threading.Thread):
        def __init__(self):
            super().__init__(daemon=True)
            self.server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))

        def run(self):
            self.server.run()

    t = UThread()
    t.start()
    # wait for server
    for _ in range(50):
        try:
            httpx.get(f"http://127.0.0.1:{port}/openapi.json")
            break
        except Exception:
            time.sleep(0.05)


def main(output: str = "attack_metrics.csv", port: int = 8019):
    _start_api(port)
    steps = 10000
    noise_levels = [0.2, 0.5, 1.0, 2.0]
    base_cfg = {"clipping_norm": 1.0, "sample_rate": 0.05, "delta": 1e-5, "accountant": "rdp"}

    epsilons, mi_accs, inv_errs = [], [], []
    for sigma in noise_levels:
        cfg = {**base_cfg, "noise_multiplier": sigma}
        r = httpx.post(f"http://127.0.0.1:{port}/dp/config", headers={"X-Role": "operator"}, json=cfg)
        r.raise_for_status()
        r = httpx.get(f"http://127.0.0.1:{port}/dp/assess", headers={"X-Role": "operator"}, params={"steps": steps})
        r.raise_for_status()
        eps = r.json()["epsilon"]
        epsilons.append(eps)
        mi_accs.append(_mi_accuracy(2000, sigma))
        inv_errs.append(_inversion_error(sigma))

    out = Path(output)
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["noise_multiplier", "epsilon", "mi_accuracy", "inversion_error"])
        for sigma, eps, acc, err in zip(noise_levels, epsilons, mi_accs, inv_errs):
            w.writerow([sigma, eps, acc, err])
    print(f"Wrote {out.resolve()}")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--output", default="attack_metrics.csv")
    p.add_argument("--port", type=int, default=8019)
    args = p.parse_args()
    main(output=args.output, port=args.port)
