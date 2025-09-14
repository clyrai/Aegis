# Example: Scikit-learn baseline

This example fits a logistic regression classifier.

What this is / is not
- Is: A very fast baseline with minimal dependencies.
- Is not: DP or FL. Use this for sanity checks and baselines.
- Is not: Orchestration. For Aegis API flows, see `technical/train_model.md`.

When to use
- Sanity-check modeling pipeline or compare to DP/FL runs.

Prerequisites
- Python deps:
  ```zsh
  pip install scikit-learn
  ```

Run it
```zsh
python examples/sklearn_demo.py --n 500 --d 5 --test_size 0.2 --seed 0
```

Output (sample)
```
Train acc: 0.92 | Test acc: 0.90
```

Notes
- Great for a quick sanity baseline before DP/FL.
