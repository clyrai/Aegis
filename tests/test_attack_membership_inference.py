from __future__ import annotations

import random


def _simulate_scores(n_train: int, n_non: int, sigma: float, seed: int = 0):
    random.seed(seed)
    # Train scores are slightly lower (better) than non-member; noise increases with sigma
    train = [random.gauss(0.4, sigma) for _ in range(n_train)]
    non = [random.gauss(0.6, sigma) for _ in range(n_non)]
    return train, non


def _attack_accuracy(train, non, threshold=0.5):
    tp = sum(1 for s in train if s < threshold)
    tn = sum(1 for s in non if s >= threshold)
    return (tp + tn) / (len(train) + len(non))


def test_membership_inference_degrades_with_noise():
    train_low, non_low = _simulate_scores(1000, 1000, sigma=0.1, seed=42)
    train_high, non_high = _simulate_scores(1000, 1000, sigma=0.6, seed=42)
    acc_low = _attack_accuracy(train_low, non_low)
    acc_high = _attack_accuracy(train_high, non_high)
    # With higher noise, attack should be closer to random (<= low-noise accuracy)
    assert acc_high <= acc_low
