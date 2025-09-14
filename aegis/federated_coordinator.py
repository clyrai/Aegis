"""
Federated Coordinator (Stage 3)

Implements a Flower-like strategy layer with Krum and Trimmed Mean aggregators,
plus a minimal authentication handshake for participant updates, straggler retry
policy, and health signaling scaffolding.

This module is designed to run with or without Flower installed. If Flower is
available, Strategy adapters can be wired; otherwise we provide a pure-Python
reference implementation for testing the aggregation & envelope logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
import hashlib
import hmac
import json
import logging
import time

try:  # optional Flower import
    import flwr as fl
except Exception:  # pragma: no cover
    fl = None


# ------------------------------- Auth Envelopes ------------------------------- #

@dataclass
class UpdateEnvelope:
    client_id: str
    round: int
    params: List[float]
    signature: str  # hex

    @staticmethod
    def sign(client_id: str, round: int, params: Sequence[float], key: bytes) -> "UpdateEnvelope":
        payload = json.dumps({"client_id": client_id, "round": round, "params": list(params)}, separators=(",", ":")).encode()
        sig = hmac.new(key, payload, hashlib.sha256).hexdigest()
        return UpdateEnvelope(client_id=client_id, round=round, params=list(params), signature=sig)

    def verify(self, key: bytes) -> bool:
        payload = json.dumps({"client_id": self.client_id, "round": self.round, "params": list(self.params)}, separators=(",", ":")).encode()
        exp = hmac.new(key, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(exp, self.signature)


# -------------------------------- Aggregators -------------------------------- #

def aggregate_trimmed_mean(updates: List[List[float]], trim_ratio: float = 0.1) -> List[float]:
    if not updates:
        return []
    n = len(updates)
    if n == 1:
        return list(updates[0])
    k = max(0, int(trim_ratio * n))
    d = len(updates[0])
    out: List[float] = []
    for j in range(d):
        col = sorted(u[j] for u in updates)
        trimmed = col[k: n - k if n - k > k else n]
        if not trimmed:
            trimmed = col
        out.append(sum(trimmed) / len(trimmed))
    return out


def aggregate_krum(updates: List[List[float]], f: int = 1) -> List[float]:
    # Basic multi-Krum: pick update with minimal sum of distances to its closest n-f-2 neighbors
    # and return it directly (or average selected set; here select 1 for simplicity).
    n = len(updates)
    if n == 0:
        return []

    def sqdist(a: List[float], b: List[float]) -> float:
        return sum((x - y) ** 2 for x, y in zip(a, b))

    m = n - f - 2
    scores: List[Tuple[float, int]] = []
    for i, ui in enumerate(updates):
        dists = [sqdist(ui, uj) for j, uj in enumerate(updates) if j != i]
        dists.sort()
        k = m if m > 0 else len(dists)
        score = sum(dists[:k])
        scores.append((score, i))
    _, best_idx = min(scores, key=lambda t: t[0])
    return list(updates[best_idx])


# ------------------------------ Coordinator Core ----------------------------- #

@dataclass
class StragglerPolicy:
    timeout_s: float = 5.0
    max_retries: int = 1


class FederatedCoordinator:
    def __init__(
        self,
        *,
        aggregator: str = "trimmed_mean",
        auth_keys: Optional[Dict[str, bytes]] = None,
        straggler: Optional[StragglerPolicy] = None,
    ) -> None:
        if aggregator not in {"trimmed_mean", "krum"}:
            raise ValueError("aggregator must be 'trimmed_mean' or 'krum'")
        self.aggregator = aggregator
        self.auth_keys = auth_keys or {}
        self.straggler = straggler or StragglerPolicy()
        self.log = logging.getLogger("aegis.federated_coordinator")

    # Envelope auth
    def verify_envelope(self, env: UpdateEnvelope) -> bool:
        key = self.auth_keys.get(env.client_id)
        ok = key is not None and env.verify(key)
        self.log.debug(
            "verify_envelope",
            extra={"client_id": env.client_id, "round": env.round, "verified": ok},
        )
        return ok

    # Aggregation
    def aggregate(self, envelopes: List[UpdateEnvelope]) -> List[float]:
        if not envelopes:
            return []
        # auth filter
        valid_updates = [e.params for e in envelopes if self.verify_envelope(e)]
        self.log.info(
            "aggregate",
            extra={
                "aggregator": self.aggregator,
                "round": envelopes[0].round,
                "received": len(envelopes),
                "valid": len(valid_updates),
            },
        )
        if not valid_updates:
            return []
        if self.aggregator == "trimmed_mean":
            return aggregate_trimmed_mean(valid_updates)
        else:
            return aggregate_krum(valid_updates)

    def aggregate_with_retries(self, envelope_attempts: List[List[UpdateEnvelope]], *, min_required: int = 1) -> List[float]:
        """Aggregate across multiple attempts to simulate straggler retries.

        Args:
            envelope_attempts: a list of batches, one per attempt (initial + retries)
            min_required: minimum number of valid updates required to proceed

        Behavior:
            - Verifies updates per attempt and accumulates valid ones.
            - Returns aggregation as soon as min_required valid updates are available.
            - If not enough updates after allowed attempts (max_retries + 1 total),
              returns aggregation of whatever valid updates were collected (or []).
        """
        valid: List[List[float]] = []
        max_attempts = max(1, int(self.straggler.max_retries) + 1)
        attempts = 0
        for batch in envelope_attempts:
            attempts += 1
            # extend valid with any newly verified updates
            for e in batch:
                if self.verify_envelope(e):
                    valid.append(e.params)
            if len(valid) >= min_required:
                return aggregate_trimmed_mean(valid) if self.aggregator == "trimmed_mean" else aggregate_krum(valid)
            if attempts >= max_attempts:
                break
            # Backoff before next attempt to simulate timeout/retry window
            try:
                time.sleep(max(0.0, float(self.straggler.timeout_s)))
            except Exception:  # pragma: no cover
                pass

        if not valid:
            return []
        return aggregate_trimmed_mean(valid) if self.aggregator == "trimmed_mean" else aggregate_krum(valid)

    # Health and stragglers (scaffolding; integration tested via examples later)
    def health_ping(self, client_id: str) -> Dict[str, str]:
        return {"client_id": client_id, "status": "ok"}


__all__ = [
    "UpdateEnvelope",
    "aggregate_trimmed_mean",
    "aggregate_krum",
    "StragglerPolicy",
    "FederatedCoordinator",
]
