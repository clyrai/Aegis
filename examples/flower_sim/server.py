from __future__ import annotations

from typing import Dict, List
from aegis.federated_coordinator import (
    FederatedCoordinator,
    UpdateEnvelope,
)


def run_round(
    aggregator: str,
    client_weights: Dict[str, List[float]],
    auth_keys: Dict[str, bytes],
    round: int = 1,
) -> List[float]:
    coord = FederatedCoordinator(aggregator=aggregator, auth_keys=auth_keys)
    envs = []
    for cid, w in client_weights.items():
        env = UpdateEnvelope.sign(client_id=cid, round=round, params=w, key=auth_keys[cid])
        envs.append(env)
    agg = coord.aggregate(envs)
    return agg


if __name__ == "__main__":
    # tiny demo with 3 clients, 4-dim params
    auth = {"c1": b"k1", "c2": b"k2", "c3": b"k3"}
    client_weights = {
        "c1": [0.9, 1.0, 1.1, 0.95],
        "c2": [1.2, 1.1, 1.0, 1.05],
        "c3": [10.0, -10.0, 10.0, -10.0],  # byzantine outlier
    }
    print("Trimmed Mean:", run_round("trimmed_mean", client_weights, auth))
    print("Krum:", run_round("krum", client_weights, auth))
