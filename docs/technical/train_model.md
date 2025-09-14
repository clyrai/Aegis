# Train a model with Aegis

This guide shows a clean, repeatable flow to train with Differential Privacy (DP) and Federated Learning (FL).

> Important
> - This is a control‑plane guide. It exercises the Aegis API (register participants, set DP, pick a strategy, start/poll, report).
> - It does NOT define a specific neural network here. By default in the dev stack, a lightweight simulator runs rounds so you can verify the orchestration and privacy accounting quickly.
> - Want a real model? Jump to "Choose your path" below and see the example model guides.

Prerequisites
- Stack running locally (see docs/technical/getting_started.md)
- Tools: `httpie` and `jq` (or use `curl` equivalents)
- Install on macOS:
  ```zsh
  brew install httpie jq
  ```

Note on models
- This guide controls the Aegis orchestration (participants, DP config, strategy, start/status/report).
- By default in the dev stack, a lightweight simulator drives rounds to validate the flow and privacy accounting.
- To run a real model end-to-end, see "Use a real model" at the end of this page.

What this guide is / is not
- Is: Orchestration workflow for DP + FL (API usage, status fields, compliance report).
- Is not: A specific model architecture tutorial (see example model pages below).

Choose your path
- "I want to validate the pipeline fast" → Stay on this page and use the simulator.
- "I want a real DP model" → Go to PyTorch + Opacus (DP): `technical/examples_pytorch_dp.md`.
- "I prefer TensorFlow" → Go to TensorFlow (non-DP baseline): `technical/examples_tensorflow.md`.
- "I need a super-quick baseline" → Go to Scikit-learn: `technical/examples_sklearn.md`.

0) Start the stack (once per session)
- Using Makefile (recommended):
  ```zsh
  make docs-up
  ```
- Or with Docker directly:
  ```zsh
  docker compose -f deploy/docker-compose.yml up -d
  ```
- Stop when finished:
  ```zsh
  make docs-down
  # or
  docker compose -f deploy/docker-compose.yml down -v
  ```

1) Register participants
- Simulated participants for a quick start:
  - `http POST :8000/participants X-Role:admin client_id=c1 key_hex=aa`
  - `http POST :8000/participants X-Role:admin client_id=c2 key_hex=bb`
  - curl equivalents:
    ```zsh
    curl -fsS -H 'X-Role: admin' -H 'Content-Type: application/json' \
      -d '{"client_id":"c1","key_hex":"aa"}' http://localhost:8000/participants | jq .
    curl -fsS -H 'X-Role: admin' -H 'Content-Type: application/json' \
      -d '{"client_id":"c2","key_hex":"bb"}' http://localhost:8000/participants | jq .
    ```

2) Configure privacy (balanced defaults)
- `http POST :8000/dp/config X-Role:operator clipping_norm:=1.0 noise_multiplier:=1.0 sample_rate:=0.01 delta:=1e-5 accountant=rdp`
  - curl:
    ```zsh
    curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
      -d '{"clipping_norm":1.0,"noise_multiplier":1.0,"sample_rate":0.01,"delta":1e-5,"accountant":"rdp"}' \
      http://localhost:8000/dp/config | jq .
    ```
- Tip: Start balanced, then tighten privacy (higher noise) once utility is confirmed.

3) Pick a federated aggregator
- Trimmed Mean (robust mean):
  - `http POST :8000/strategy X-Role:operator strategy=trimmed_mean`
- Krum (Byzantine‑resilient):
  - `http POST :8000/strategy X-Role:operator strategy=krum`
  - curl:
    ```zsh
    curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
      -d '{"strategy":"trimmed_mean"}' http://localhost:8000/strategy | jq .
    curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
      -d '{"strategy":"krum"}' http://localhost:8000/strategy | jq .
    ```

4) Start training
- `http POST :8000/training/start X-Role:operator session_id=run1 rounds:=5`
  - curl:
    ```zsh
    curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
      -d '{"session_id":"run1","rounds":5}' http://localhost:8000/training/start | jq .
    ```
- Optional: check status:
  - `http GET :8000/training/status X-Role:viewer session_id==run1`
  - curl:
    ```zsh
    curl -fsS -H 'X-Role: viewer' "http://localhost:8000/training/status?session_id=run1" | jq .
    ```
  - Sample response (values will vary):
    ```json
    {
      "session_id": "run1",
      "status": "running",
      "current_round": 2,
      "total_rounds": 5,
      "eta_seconds": 3.2,
      "epsilon_estimate": 0.0001
    }
    ```
- Watch until complete (optional):
  ```zsh
  for i in {1..20}; do
    curl -fsS -H 'X-Role: viewer' "http://localhost:8000/training/status?session_id=run1" | jq -r '.status, ("round " + (.current_round|tostring) + "/" + (.total_rounds|tostring))'
    sleep 1
  done
    ```

5) Monitor progress
- Grafana: http://localhost:3000
- Look at request rates, latency, scrape health, epsilon consumption (if charted)

6) Generate a compliance report
- `http GET :8000/compliance/report X-Role:viewer > ./report_run1.md`
  - curl:
    ```zsh
    curl -fsS -H 'X-Role: viewer' http://localhost:8000/compliance/report | jq -r .markdown > ./report_run1.md
    ```
- Share this with non‑technical stakeholders.

Tips
- Use Krum if you expect some participants to be unreliable or adversarial.
- Track epsilon: lower epsilon = stronger privacy but more noise; find your sweet spot.
- Keep audit logs for your reviews.

Try it (automated)
- With Docker running:
  ```zsh
  make test-train SESSION_ID=smoke ROUNDS=3
  ```
  This will start the stack if needed, run the flow above, and write a report to `test_artifacts/`.

Use a real model
- PyTorch + Opacus (DP-SGD):
  - Guide: technical/examples_pytorch_dp.md
  - Quick run:
    ```zsh
    pip install torch opacus
    python examples/pytorch_opacus_demo.py --epochs 5 --batch_size 64 --lr 0.1 \
      --noise_multiplier 1.0 --max_grad_norm 1.0 --delta 1e-5 --seed 0
    ```
- TensorFlow (non-DP baseline):
  - Guide: technical/examples_tensorflow.md
  - Quick run:
    ```zsh
    pip install tensorflow
    python examples/tensorflow_demo.py --epochs 5 --batch_size 64 --lr 0.1 --hidden 8 --seed 0
    ```
- Scikit-learn baseline:
  - Guide: technical/examples_sklearn.md
  - Quick run:
    ```zsh
    pip install scikit-learn
    python examples/sklearn_demo.py --n 500 --d 5 --test_size 0.2 --seed 0
    ```
