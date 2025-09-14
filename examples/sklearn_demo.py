from __future__ import annotations

import argparse

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
except Exception:  # pragma: no cover - optional
    print("Install scikit-learn to run this demo: pip install scikit-learn")
    raise SystemExit(0)


def main():
    parser = argparse.ArgumentParser(description="Scikit-learn baseline demo")
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--d", type=int, default=5)
    parser.add_argument("--test_size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    X, y = make_classification(n_samples=args.n, n_features=args.d, random_state=args.seed)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=args.test_size, random_state=args.seed)
    clf = LogisticRegression(max_iter=200)
    clf.fit(X_train, y_train)
    preds_train = clf.predict(X_train)
    preds_test = clf.predict(X_test)
    print(
        f"Train acc: {accuracy_score(y_train, preds_train):.3f} | Test acc: {accuracy_score(y_test, preds_test):.3f}"
    )


if __name__ == "__main__":
    main()
