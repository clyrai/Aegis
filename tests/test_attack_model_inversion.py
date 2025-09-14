from __future__ import annotations

import random


def _make_private_stat(mean: float, sigma: float, n: int, seed: int = 0) -> float:
    random.seed(seed)
    noise = random.gauss(0, sigma / max(n, 1))
    return mean + noise


def test_model_inversion_error_increases_with_noise():
    true_mean = 0.7
    priv_low = _make_private_stat(true_mean, sigma=0.1, n=1000, seed=1)
    priv_high = _make_private_stat(true_mean, sigma=1.0, n=1000, seed=1)
    err_low = abs(priv_low - true_mean)
    err_high = abs(priv_high - true_mean)
    assert err_high >= err_low
