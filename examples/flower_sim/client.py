from __future__ import annotations

import random
from typing import List

from .dataset import make_toy_dataset


def local_train(weights: List[float], lr: float = 0.1, steps: int = 5, seed: int = 0) -> List[float]:
    random.seed(seed)
    X, y = make_toy_dataset(n=50, d=len(weights), seed=seed)
    w = list(weights)
    for _ in range(steps):
        # simple perceptron-like update
        for xi, yi in zip(X, y):
            pred = 1 if sum(a * b for a, b in zip(w, xi)) > 0 else 0
            err = yi - pred
            for j in range(len(w)):
                w[j] += lr * err * xi[j]
    return w
