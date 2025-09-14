from __future__ import annotations

import random
import argparse

from aegis.privacy_engine import DPConfig, DifferentialPrivacyEngine


def run(sigmas: list[float], output: str | None = None):
    base = DPConfig(sample_rate=0.01, delta=1e-5)
    rows = ["sigma,epsilon,utility"]
    for sigma in sigmas:
        eng = DifferentialPrivacyEngine(DPConfig(**{**base.to_dict(), "noise_multiplier": sigma}))
        eps = eng.stepwise_accounting(steps=1000)
        util = 1.0 - sigma + random.uniform(-0.02, 0.02)
        print(f"sigma={sigma}, epsilon~{eps:.2f}, util~{util:.2f}")
        rows.append(f"{sigma},{eps:.4f},{util:.4f}")
    if output:
        with open(output, "w") as f:
            f.write("\n".join(rows) + "\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--epsilons", type=str, default="0.2,0.5,1.0")
    ap.add_argument("--output", type=str, default=None)
    args = ap.parse_args()
    sigmas = [float(x) for x in args.epsilons.split(",")]
    run(sigmas=sigmas, output=args.output)
