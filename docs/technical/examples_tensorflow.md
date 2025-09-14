# Example: TensorFlow (non-DP)

This example trains a tiny Keras MLP on synthetic data.

What this is / is not
- Is: A minimal Keras baseline with accuracy metrics and reproducibility.
- Is not: A DP example. For DP with TF, consider integrating `tensorflow-privacy`.
- Is not: The orchestration walkthrough. For register/start/status/report, see `technical/train_model.md`.

When to use
- Quick neural baseline for TensorFlow users.
- Prior to adding DP (swap in TF-Privacy optimizer later).

Prerequisites
- Python deps:
  ```zsh
  pip install tensorflow
  ```

Run it
```zsh
python examples/tensorflow_demo.py --epochs 5 --batch_size 64 --lr 0.1 --hidden 8 --seed 0
```

Output (sample)
```
Train acc: 0.86 | Test acc: 0.84
```

Notes
- This is a non-DP baseline. For DP with TensorFlow, integrate `tensorflow-privacy`.
