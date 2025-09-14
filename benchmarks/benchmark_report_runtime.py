from __future__ import annotations

import time
import argparse

from aegis.compliance.report import generate_markdown
from aegis.privacy_engine import DPConfig


def run(iterations: int = 1, output: str | None = None):
    cfg = DPConfig(noise_multiplier=1.0, sample_rate=0.01, delta=1e-5)
    participants = {f"c{i}": b"k" for i in range(3)}
    sessions = {"demo": {"status": "stopped", "rounds": "3"}}
    totals = []
    for _ in range(iterations):
        t0 = time.time()
        _ = generate_markdown(dp_config=cfg, participants=participants, sessions=sessions, strategy="trimmed_mean")
        totals.append(time.time() - t0)
    avg = sum(totals) / len(totals)
    print(f"report_seconds_avg={avg:.5f}")
    if output:
        with open(output, "w") as f:
            f.write("metric,value\n")
            f.write(f"report_seconds_avg,{avg:.6f}\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations", type=int, default=1)
    ap.add_argument("--output", type=str, default=None)
    args = ap.parse_args()
    run(iterations=args.iterations, output=args.output)
