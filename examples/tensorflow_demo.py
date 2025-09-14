from __future__ import annotations

import argparse

try:
    import tensorflow as tf
except Exception:  # pragma: no cover - optional
    print("Install tensorflow to run this demo: pip install tensorflow")
    raise SystemExit(0)


def make_synthetic(n: int = 512, d: int = 4, seed: int = 0):
    tf.random.set_seed(seed)
    X = tf.random.normal((n, d))
    y = tf.cast(tf.reduce_sum(X, axis=1) > 0, tf.int32)
    return X, y


def main():
    parser = argparse.ArgumentParser(description="TensorFlow demo (non-DP)")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.1)
    parser.add_argument("--hidden", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    X, y = make_synthetic(n=512, d=4, seed=args.seed)
    n_train = int(0.8 * X.shape[0])
    X_train, y_train = X[:n_train], y[:n_train]
    X_test, y_test = X[n_train:], y[n_train:]

    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(4,)),
        tf.keras.layers.Dense(args.hidden, activation='relu'),
        tf.keras.layers.Dense(2)
    ])
    model.compile(
        optimizer=tf.keras.optimizers.SGD(learning_rate=args.lr),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=["accuracy"],
    )
    model.fit(X_train, y_train, epochs=args.epochs, batch_size=args.batch_size, verbose=0)
    train_loss, train_acc = model.evaluate(X_train, y_train, verbose=0)
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"Train acc: {train_acc:.3f} | Test acc: {test_acc:.3f}")


if __name__ == "__main__":
    main()
