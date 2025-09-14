# Example: PyTorch + Opacus (DP)

This example trains a small MLP with Differential Privacy using Opacus.

What this is / is not
- Is: A real DP-SGD training example with epsilon estimation and accuracy metrics.
- Is not: The Aegis orchestration walkthrough. For register/start/status/report, see `technical/train_model.md`.

When to use
- Demonstrate privacy-utility tradeoffs and epsilon accounting with a real model.
- Validate DP tuning knobs: `noise_multiplier`, `max_grad_norm`, `batch_size`, `epochs`.

Prerequisites
- Python deps:
  ```zsh
  pip install torch opacus
  ```

Run it
```zsh
python examples/pytorch_opacus_demo.py --epochs 5 --batch_size 64 --lr 0.1 \
  --noise_multiplier 1.0 --max_grad_norm 1.0 --delta 1e-5 --seed 0
```

Output (sample)
```
Train acc: 0.800 | Test acc: 0.770 | Epsilon≈0.XXXX (delta=1e-05)
```

Notes
- Increase `noise_multiplier` to strengthen privacy (epsilon decreases) but expect more utility loss.
- `max_grad_norm` controls per-sample clipping; tune alongside `noise_multiplier`.
 - Need orchestration (participants/strategy/status/report)? See `technical/train_model.md`.
