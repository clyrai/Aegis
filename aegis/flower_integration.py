"""
Optional Flower integration for Aegis.

Provides a Strategy adapter that reuses Aegis's FederatedCoordinator aggregators
and CLI-callable helpers to start a Flower server/client. All imports are lazy
and will raise a clear RuntimeError if Flower (and NumPy) are not installed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .federated_coordinator import FederatedCoordinator


def is_flower_available() -> bool:
    try:
        import flwr  # noqa: F401
        return True
    except Exception:
        return False


def _require_flower() -> None:
    if not is_flower_available():
        raise RuntimeError("Flower integration requires 'flwr' to be installed. See docs for installation.")


def _require_numpy():
    try:
        import numpy  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise RuntimeError("Flower integration requires 'numpy' for parameter conversions.") from e


def start_flower_server(
    *,
    server_address: str = "127.0.0.1:8080",
    aggregator: str = "trimmed_mean",
    rounds: int = 3,
    auth_keys: Optional[Dict[str, bytes]] = None,
) -> None:
    """Start a Flower server using Aegis aggregators.

    Parameters
    - server_address: host:port for the Flower gRPC server
    - aggregator: 'trimmed_mean' or 'krum'
    - rounds: number of federated rounds
    - auth_keys: optional per-client HMAC keys for envelope verification (not enforced at Flower layer)
    """
    _require_flower()
    _require_numpy()

    import flwr as fl
    from flwr.common import parameters_to_ndarrays, ndarrays_to_parameters

    coord = FederatedCoordinator(aggregator=aggregator, auth_keys=auth_keys or {})

    class AegisStrategy(fl.server.strategy.FedAvg):  # runtime dependency on flwr
        def __init__(self):
            super().__init__()
            self._shapes: Optional[List[Tuple[int, ...]]] = None

        def aggregate_fit(self, server_round: int, results: Any, failures: Any):
            if not results:
                return None, {}

            # Convert Flower Parameters -> list of lists while tracking shapes
            weights: List[List[float]] = []
            shapes: Optional[List[Tuple[int, ...]]] = None
            import numpy as np

            for _, fit_res in results:
                nds = parameters_to_ndarrays(fit_res.parameters)
                if shapes is None:
                    shapes = [tuple(arr.shape) for arr in nds]
                flat: List[float] = []
                for arr in nds:
                    flat.extend(np.asarray(arr).reshape(-1).astype("float64").tolist())
                weights.append(flat)

            # Aggregate using Aegis aggregators
            if coord.aggregator == "trimmed_mean":
                from .federated_coordinator import aggregate_trimmed_mean

                agg_flat = aggregate_trimmed_mean(weights)
            else:
                from .federated_coordinator import aggregate_krum

                agg_flat = aggregate_krum(weights)

            # Reconstruct parameter shapes to return to Flower
            if self._shapes is None:
                self._shapes = shapes or []
            idx = 0
            nds_out: List[Any] = []
            for shp in self._shapes:
                size = 1
                for s in shp:
                    size *= s
                chunk = agg_flat[idx: idx + size]
                idx += size
                nds_out.append(np.array(chunk, dtype="float64").reshape(shp))
            params = ndarrays_to_parameters(nds_out)
            return params, {}

    strategy = AegisStrategy()
    fl.server.start_server(server_address=server_address, strategy=strategy, config=fl.server.ServerConfig(num_rounds=rounds))


def start_flower_client(
    *,
    server_address: str = "127.0.0.1:8080",
    dim: int = 8,
    steps: int = 20,
    lr: float = 0.1,
    seed: int = 0,
) -> None:
    """Start a simple Flower NumPyClient that trains a tiny local model using Aegis example logic."""
    _require_flower()
    _require_numpy()

    import numpy as np
    import flwr as fl

    # Local weights are a single vector
    from examples.flower_sim.client import local_train

    class AegisClient(fl.client.NumPyClient):  # runtime dependency on flwr
        def __init__(self):
            self.w = np.zeros((dim,), dtype="float64")

        def get_parameters(self, config: Dict[str, Any]):
            return [self.w]

        def fit(self, parameters: List[Any], config: Dict[str, Any]):
            (w,) = parameters  # one vector
            self.w = w.astype("float64")
            # Train via our toy local trainer
            new_w_list: List[float] = local_train(self.w.tolist(), lr=lr, steps=steps, seed=seed)
            self.w = np.array(new_w_list, dtype="float64")
            return [self.w], len(self.w), {}

        def evaluate(self, parameters: List[Any], config: Dict[str, Any]):
            # No-op evaluation
            return 0.0, len(self.w), {}

    fl.client.start_numpy_client(server_address, client=AegisClient())
