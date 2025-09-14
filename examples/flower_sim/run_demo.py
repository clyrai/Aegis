from __future__ import annotations

import argparse
from typing import Dict, List

from .client import local_train
from .server import run_round


def main(rounds: int = 1) -> None:
    # Simulate a single aggregation run using both strategies
    init = [0.0, 0.0, 0.0, 0.0]
    auth = {"c1": b"k1", "c2": b"k2", "c3": b"k3"}

    for r in range(rounds):
        client_weights: Dict[str, List[float]] = {
            cid: local_train(init, seed=r + i)
            for i, cid in enumerate(["c1", "c2", "c3"], start=1)
        }

        agg_tm = run_round("trimmed_mean", client_weights, auth)
        agg_krum = run_round("krum", client_weights, auth)

        print(f"Round {r}")
        print("Aggregated (Trimmed Mean):", agg_tm)
        print("Aggregated (Krum):", agg_krum)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=1)
    args = parser.parse_args()
    main(rounds=args.rounds)
