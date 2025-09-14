import json
import pytest

from aegis.privacy_engine import DPConfig, DifferentialPrivacyEngine


def test_config_serialization_roundtrip():
    cfg = DPConfig(clipping_norm=1.2, noise_multiplier=0.7, sample_rate=0.02, delta=1e-6)
    d = cfg.to_dict()
    s = json.dumps(d)
    loaded = DPConfig.from_dict(json.loads(s))
    assert loaded == cfg


def test_stepwise_accounting_monotonic():
    engine = DifferentialPrivacyEngine(DPConfig(noise_multiplier=1.0, sample_rate=0.01, delta=1e-5))
    eps1 = engine.stepwise_accounting(steps=10)
    eps2 = engine.stepwise_accounting(steps=100)
    assert eps1 >= 0
    assert eps2 >= eps1


def test_epsilon_targeting_finds_sigma():
    engine = DifferentialPrivacyEngine(DPConfig(noise_multiplier=0.5, sample_rate=0.01, delta=1e-5))
    # target epsilon reasonably small for 100 steps
    eps, sigma = engine.epsilon_targeting(epsilon_target=2.0, steps=100)
    assert eps > 0
    assert sigma > 0
    # After targeting, stepwise epsilon should be close (not exceeding target by large margin)
    eps_after = engine.stepwise_accounting(steps=100)
    assert eps_after <= eps + 1e-6


@pytest.mark.parametrize("sigma_stronger, sigma_weaker", [(2.5, 0.5), (3.0, 1.0)])
def test_stronger_privacy_decreases_utility_proxy(sigma_stronger, sigma_weaker):
    # Use a toy utility proxy directly related to epsilon for a fixed step count
    # (i.e., stricter privacy (lower epsilon) => lower utility), matching acceptance criteria.
    steps = 200
    base_cfg = DPConfig(sample_rate=0.01, delta=1e-5)
    eng_strong = DifferentialPrivacyEngine(DPConfig(**{**base_cfg.to_dict(), "noise_multiplier": sigma_stronger}))
    eng_weak = DifferentialPrivacyEngine(DPConfig(**{**base_cfg.to_dict(), "noise_multiplier": sigma_weaker}))

    eps_strong = eng_strong.stepwise_accounting(steps)
    eps_weak = eng_weak.stepwise_accounting(steps)

    # Stronger privacy -> lower epsilon
    assert eps_strong < eps_weak

    # Utility proxy: epsilon / (1 + epsilon) in [0, 1)
    util_strong = eps_strong / (1.0 + eps_strong)
    util_weak = eps_weak / (1.0 + eps_weak)

    assert util_strong < util_weak
