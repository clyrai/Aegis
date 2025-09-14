from __future__ import annotations

import time
import random
import argparse

def run(rounds: int = 10, clients: int = 5, output: str | None = None):
    start = time.time()
    w = [0.0] * 10
    for _ in range(rounds):
        updates = [[wi + random.uniform(-0.01, 0.01) for wi in w] for _ in range(clients)]
        # simple average
        w = [sum(col) / len(col) for col in zip(*updates)]
    dur = time.time() - start
    line = f"rounds={rounds}, clients={clients}, seconds={dur:.4f}"
    print(line)
    if output:
        with open(output, "w") as f:
            f.write("metric,value\n")
            f.write(f"seconds,{dur:.6f}\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--clients", type=int, default=5)
    ap.add_argument("--output", type=str, default=None)
    args = ap.parse_args()
    run(rounds=args.rounds, clients=args.clients, output=args.output)
