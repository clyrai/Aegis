from __future__ import annotations

import random
from typing import List, Tuple


def make_toy_dataset(n: int = 100, d: int = 5, seed: int = 0) -> Tuple[List[List[float]], List[int]]:
    random.seed(seed)
    X = [[random.uniform(-1, 1) for _ in range(d)] for _ in range(n)]
    y = [1 if sum(x) + random.uniform(-0.2, 0.2) > 0 else 0 for x in X]
    return X, y
