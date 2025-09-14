from __future__ import annotations


from aegis.federated_coordinator import FederatedCoordinator, StragglerPolicy, UpdateEnvelope


def _keys():
    return {"c1": bytes.fromhex("aa"), "c2": bytes.fromhex("bb"), "c3": bytes.fromhex("cc")}


def test_krum_aggregate_with_retries_picks_consensus_over_outlier():
    keys = _keys()
    coord = FederatedCoordinator(aggregator="krum", auth_keys=keys, straggler=StragglerPolicy(timeout_s=0.0, max_retries=2))
    # attempt 1: only c1 arrives
    a1 = [UpdateEnvelope.sign("c1", 1, [0.0, 0.0], keys["c1"])]
    # attempt 2: c2 is an outlier; c3 is close to c1
    a2 = [
        UpdateEnvelope.sign("c2", 1, [10.0, 10.0], keys["c2"]),
        UpdateEnvelope.sign("c3", 1, [0.5, 0.5], keys["c3"]),
    ]
    out = coord.aggregate_with_retries([a1, a2], min_required=2)
    # Krum should pick a non-outlier (either c1 or c3). Both are < 1.0 distance from each other.
    assert out[0] < 1.0 and out[1] < 1.0


def test_krum_returns_empty_if_all_invalid():
    keys = _keys()
    coord = FederatedCoordinator(aggregator="krum", auth_keys=keys, straggler=StragglerPolicy(timeout_s=0.0, max_retries=1))
    a1 = [UpdateEnvelope.sign("cX", 1, [100.0, 100.0], b"00")]
    a2 = [UpdateEnvelope.sign("cY", 1, [100.0, 100.0], b"00")]
    out = coord.aggregate_with_retries([a1, a2], min_required=2)
    assert out == []
