---
title: Aegis for Beginners (A–Z)
---

# Aegis for Beginners (A–Z)

Welcome! This guide is for non‑technical users and beginners. In a few minutes, you’ll run a small demo, watch training progress, and generate a compliance report you can share with stakeholders.

What you’ll do
- Start Aegis locally with one command
- Run a short training session (simulated) to see how things work
- Watch live progress in a dashboard
- Generate and save a compliance report (Markdown or PDF)

What Aegis is (in plain language)
- Differential Privacy (DP): Adds carefully calibrated “noise” so individual records stay private while the overall model still learns.
- Federated Learning (FL): Trains across multiple participants without centralizing raw data.
- Aegis orchestrates DP + FL and produces reports for compliance and audit.

Before you start (macOS)
- Install Docker Desktop: https://www.docker.com/products/docker-desktop/
- Open Docker Desktop so it’s running in the background.
- Optional: Install `jq` for pretty output:
  ```zsh
  brew install jq
  ```

1) Start the demo
- Recommended: use our make target. In Terminal:
  ```zsh
  make demo-up
  ```
- If you prefer Docker directly:
  ```zsh
  docker compose -f deploy/docker-compose.yml up -d
  ```

2) Check it’s running
```zsh
curl -fsS http://localhost:8000/healthz
```
Expected: `{ "status": "ok" }`

3) Open the dashboard
```zsh
open http://localhost:3000
```
Tip: Grafana shows basic API health and activity; it will look more lively after you start training.

4) Run a short training session (one‑command demo)
This simulates a small training run and writes a compliance report to `test_artifacts/`.
```zsh
make test-train SESSION_ID=beginners ROUNDS=3
```
What happens:
- Registers two demo participants (no real data moves)
- Applies default privacy settings
- Starts a short training session
- Saves `test_artifacts/report_beginners.md`

5) Watch progress (optional)
- Live status via API:
  ```zsh
  curl -fsS -H 'X-Role: viewer' 'http://localhost:8000/training/status?session_id=beginners' | jq .
  ```
- Dashboard (Grafana):
  - It may take a minute for panels to populate with activity.

6) Generate a compliance report (manually)
- Markdown (JSON → Markdown extract):
  ```zsh
  curl -fsS -H 'X-Role: viewer' http://localhost:8000/compliance/report | jq -r .markdown > report.md
  open report.md
  ```
- PDF (if you prefer):
  ```zsh
  curl -fsS -H 'X-Role: viewer' 'http://localhost:8000/compliance/report?format=pdf' > report.pdf
  open report.pdf
  ```

How to read the report (simple)
- Epsilon (ε): Lower ε means stronger privacy (more protection), but usually less model accuracy.
- DP settings: Show clipping, noise, sample rate, and accountant method used.
- Training summary: Who participated, when, which aggregation strategy, versions.
- Use this in governance or external reviews (it’s human‑readable).

7) Stop the demo
```zsh
make demo-down
# or
docker compose -f deploy/docker-compose.yml down -v
```

Common issues (and quick fixes)
- Docker not running: Open Docker Desktop first, then retry.
- Ports in use (8000/3000/9090): Close other apps using those ports, or edit ports in `deploy/docker-compose.yml`.
- `jq: command not found`: Install with `brew install jq` (macOS).
- Slow dashboard updates: Wait 30–60 seconds for activity to appear; refresh the browser.

Next steps
- 5‑minute Quick Tour: `docs/basics/quick_tour.md` — the essentials, fast.
- Train via API (control‑plane): `docs/technical/train_model.md`
- Compliance details and examples: `docs/technical/compliance_reports.md`
- Run locally with Docker Compose: `docs/technical/local_docker_compose.md`
- Real models (examples):
  - PyTorch + Opacus (DP): `docs/technical/examples_pytorch_dp.md`
  - TensorFlow baseline: `docs/technical/examples_tensorflow.md`
  - Scikit‑learn baseline: `docs/technical/examples_sklearn.md`

Glossary (two lines each)
- Participant: An organization (or device) that trains locally and shares updates, not raw data.
- Aggregator: How updates are combined; e.g., Trimmed Mean (robust), Krum (Byzantine‑tolerant).
- DP Accountant: Tracks privacy budget (ε, δ) as training progresses.

That’s it! You’ve run Aegis end‑to‑end and produced a shareable compliance report.
