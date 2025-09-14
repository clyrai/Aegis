from __future__ import annotations

import pytest

from aegis.federated_coordinator import FederatedCoordinator, StragglerPolicy, UpdateEnvelope


def _keys():
    return {"c1": bytes.fromhex("aa"), "c2": bytes.fromhex("bb"), "c3": bytes.fromhex("cc")}


def test_aggregate_with_retries_accumulates_until_min_required():
    keys = _keys()
    coord = FederatedCoordinator(aggregator="trimmed_mean", auth_keys=keys, straggler=StragglerPolicy(timeout_s=0.1, max_retries=2))
    # attempt 1: only c1 arrives
    a1 = [UpdateEnvelope.sign("c1", 1, [1.0, 1.0], keys["c1"])]
    # attempt 2: c2 arrives
    a2 = [UpdateEnvelope.sign("c2", 1, [3.0, 5.0], keys["c2"])]
    # attempt 3: c3 invalid signature (simulate still down) and then one valid
    bad = UpdateEnvelope.sign("c3", 1, [100.0, 100.0], b"00")
    a3 = [bad, UpdateEnvelope.sign("c3", 1, [5.0, 9.0], keys["c3"])]

    out = coord.aggregate_with_retries([a1, a2, a3], min_required=2)
    # After first two valid updates (c1 and c2), trimmed mean of [[1,1],[3,5]] = [2,3]
    assert out == pytest.approx([2.0, 3.0])


def test_aggregate_with_retries_returns_empty_if_none_valid():
    keys = _keys()
    coord = FederatedCoordinator(aggregator="trimmed_mean", auth_keys=keys, straggler=StragglerPolicy(timeout_s=0.1, max_retries=1))
    # all attempts invalid
    a1 = [UpdateEnvelope.sign("cX", 1, [10.0, 10.0], b"ff")]
    a2 = [UpdateEnvelope.sign("cY", 1, [11.0, 11.0], b"ff")]
    out = coord.aggregate_with_retries([a1, a2], min_required=2)
    assert out == []


def test_backoff_waits_between_attempts(monkeypatch):
    # Ensure coordinator calls sleep between attempts according to timeout_s
    calls = {"sleep": 0, "args": []}

    def fake_sleep(s):
        calls["sleep"] += 1
        calls["args"].append(s)

    monkeypatch.setattr("aegis.federated_coordinator.time.sleep", fake_sleep)

    keys = _keys()
    coord = FederatedCoordinator(aggregator="trimmed_mean", auth_keys=keys, straggler=StragglerPolicy(timeout_s=0.05, max_retries=2))
    # Provide attempts that never reach min_required to force full retry loop
    a1 = [UpdateEnvelope.sign("cX", 1, [0.0], b"00")]
    a2 = [UpdateEnvelope.sign("cY", 1, [0.0], b"00")]
    a3 = [UpdateEnvelope.sign("cZ", 1, [0.0], b"00")]
    _ = coord.aggregate_with_retries([a1, a2, a3], min_required=2)
    # With max_retries=2, attempts=3; sleep should be called between attempt1->2 and 2->3
    assert calls["sleep"] >= 2
    assert all(arg >= 0.05 for arg in calls["args"][:2])
