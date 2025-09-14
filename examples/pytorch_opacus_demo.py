from __future__ import annotations

import argparse
from typing import Tuple

try:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset
    from opacus import PrivacyEngine  # type: ignore
except Exception:  # pragma: no cover - optional
    print("Install torch and opacus to run this demo: pip install torch opacus")
    raise SystemExit(0)


def make_synthetic(n: int = 512, d: int = 4, seed: int = 0) -> Tuple[torch.Tensor, torch.Tensor]:
    torch.manual_seed(seed)
    X = torch.randn(n, d)
    y = (X.sum(dim=1) > 0).long()
    return X, y


def accuracy(model: nn.Module, X: torch.Tensor, y: torch.Tensor) -> float:
    with torch.no_grad():
        logits = model(X)
        preds = logits.argmax(dim=1)
        return (preds == y).float().mean().item()


def main():
    parser = argparse.ArgumentParser(description="PyTorch + Opacus DP demo")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.1)
    parser.add_argument("--noise_multiplier", type=float, default=1.0)
    parser.add_argument("--max_grad_norm", type=float, default=1.0)
    parser.add_argument("--delta", type=float, default=1e-5)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    # data
    X, y = make_synthetic(n=512, d=4, seed=args.seed)
    n_train = int(0.8 * len(X))
    X_train, y_train = X[:n_train], y[:n_train]
    X_test, y_test = X[n_train:], y[n_train:]
    train_ds = TensorDataset(X_train, y_train)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)

    # model & optimizer
    model = nn.Sequential(nn.Linear(4, 8), nn.ReLU(), nn.Linear(8, 2))
    optimizer = torch.optim.SGD(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()

    # Differential Privacy via Opacus
    privacy_engine = PrivacyEngine()
    model, optimizer, train_loader = privacy_engine.make_private(
        module=model,
        optimizer=optimizer,
        data_loader=train_loader,
        noise_multiplier=args.noise_multiplier,
        max_grad_norm=args.max_grad_norm,
    )

    # training
    model.train()
    for _ in range(args.epochs):
        for xb, yb in train_loader:
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()

    # eval & epsilon
    model.eval()
    acc_train = accuracy(model, X_train, y_train)
    acc_test = accuracy(model, X_test, y_test)
    try:
        # Opacus 1.x
        eps = privacy_engine.get_epsilon(args.delta)  # type: ignore[attr-defined]
    except Exception:
        try:
            # Newer API via accountant
            eps = privacy_engine.accountant.get_epsilon(args.delta)  # type: ignore[attr-defined]
        except Exception:
            eps = float("nan")

    print(f"Train acc: {acc_train:.3f} | Test acc: {acc_test:.3f} | Epsilon≈{eps:.4f} (delta={args.delta})")


if __name__ == "__main__":
    main()
