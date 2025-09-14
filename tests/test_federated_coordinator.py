from __future__ import annotations

from aegis.federated_coordinator import (
    FederatedCoordinator,
    UpdateEnvelope,
    aggregate_trimmed_mean,
    aggregate_krum,
)


def test_trimmed_mean_basic():
    updates = [
        [1.0, 2.0, 3.0],
        [1.1, 2.1, 3.1],
        [100.0, -100.0, 100.0],  # outlier
        [0.9, 1.9, 2.9],
    ]
    agg = aggregate_trimmed_mean(updates, trim_ratio=0.25)
    assert len(agg) == 3
    # Result should be close to mean of non-outliers ~ [1.0, 2.0, 3.0]
    assert abs(agg[0] - 1.0) < 0.1


def test_krum_picks_consensus_like_update():
    updates = [
        [1.0, 2.0],
        [1.05, 1.95],
        [50.0, -50.0],  # byzantine
        [0.95, 2.05],
    ]
    agg = aggregate_krum(updates, f=1)
    assert len(agg) == 2
    assert abs(agg[0] - 1.0) < 0.2


def test_envelope_auth_and_coordination():
    auth = {"c1": b"k1", "c2": b"k2", "c3": b"k3"}
    coord = FederatedCoordinator(aggregator="trimmed_mean", auth_keys=auth)
    envs = [
        UpdateEnvelope.sign("c1", 1, [1.0, 2.0], auth["c1"]),
        UpdateEnvelope.sign("c2", 1, [1.1, 1.9], auth["c2"]),
        # forged client with wrong key/signature
        UpdateEnvelope(client_id="cX", round=1, params=[100.0, -100.0], signature="deadbeef"),
    ]
    agg = coord.aggregate(envs)
    assert len(agg) == 2
    # outlier should be ignored by auth filter
    assert agg[0] < 10
