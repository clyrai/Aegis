---
title: Aegis like a Professional (A–Z)
---

# Aegis like a Professional (A–Z)

This guide is for users who want a complete, repeatable workflow—end to end. You’ll bring the system up, onboard participants, register dataset metadata, configure privacy, select a federated strategy, run and monitor training, generate a compliance report, and export audit logs.

Assumptions
- You’re on macOS with zsh and Docker Desktop installed.
- You can run commands in Terminal and optionally install small tools (`jq`, `httpie`).

Tools (recommended)
```zsh
brew install jq httpie
```

0) Start the platform
```zsh
make demo-up
# or
docker compose -f deploy/docker-compose.yml up -d
```
Health checks:
```zsh
curl -fsS :8000/healthz
open http://localhost:3000   # Grafana
```

1) Onboard participants
Register two demo participants. These are simulated keys for local runs.
```zsh
http POST :8000/participants X-Role:admin client_id=c1 key_hex=aa
http POST :8000/participants X-Role:admin client_id=c2 key_hex=bb

# curl equivalents
curl -fsS -H 'X-Role: admin' -H 'Content-Type: application/json' \
  -d '{"client_id":"c1","key_hex":"aa"}' :8000/participants | jq .
curl -fsS -H 'X-Role: admin' -H 'Content-Type: application/json' \
  -d '{"client_id":"c2","key_hex":"bb"}' :8000/participants | jq .
```

2) Register dataset metadata (optional but recommended)
Capture basic information used for data quality and alignment checks.
```zsh
curl -fsS -H 'X-Role: admin' -H 'Content-Type: application/json' \
  -d '{
        "client_id":"c1",
        "num_samples":500,
        "num_features":10,
        "missing_fraction":0.0,
        "class_counts": {"0":450, "1":50},
        "schema":["f1","f2","f3"]
      }' :8000/dataset/register | jq .

curl -fsS -H 'X-Role: admin' -H 'Content-Type: application/json' \
  -d '{
        "client_id":"c2",
        "num_samples":600,
        "num_features":10,
        "missing_fraction":0.01,
        "class_counts": {"0":540, "1":60},
        "schema":["f1","f2","f3"]
      }' :8000/dataset/register | jq .
```

3) Configure Differential Privacy (DP)
Set a balanced starting point. You can tighten privacy later by increasing `noise_multiplier`.
```zsh
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
  -d '{"clipping_norm":1.0, "noise_multiplier":1.0, "sample_rate":0.01, "delta":1e-5, "accountant":"rdp"}' \
  :8000/dp/config | jq .
```

4) Pick a federated aggregation strategy
Trimmed Mean is robust; Krum is more Byzantine-tolerant.
```zsh
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
  -d '{"strategy":"trimmed_mean"}' :8000/strategy | jq .

# or
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
  -d '{"strategy":"krum"}' :8000/strategy | jq .
```

5) Start training
Choose a `session_id` you’ll re-use for status and reporting.
```zsh
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
  -d '{"session_id":"pro-run-1","rounds":5}' :8000/training/start | jq .
```

6) Monitor progress
- API status:
  ```zsh
  curl -fsS -H 'X-Role: viewer' ':8000/training/status?session_id=pro-run-1' | jq .
  ```
- Grafana dashboards:
  ```zsh
  open http://localhost:3000
  ```
- Optional: watch loop (stops after a few checks):
  ```zsh
  for i in {1..10}; do
    curl -fsS -H 'X-Role: viewer' ':8000/training/status?session_id=pro-run-1' | jq -r '.status+" r:"+(.current_round|tostring)+"/"+(.total_rounds|tostring)';
    sleep 2;
  done
  ```

7) Generate compliance report
- Markdown (recommended for sharing in docs or tickets):
  ```zsh
  curl -fsS -H 'X-Role: viewer' :8000/compliance/report | jq -r .markdown > report_pro_run_1.md
  open report_pro_run_1.md
  ```
- PDF (if needed for executive audiences):
  ```zsh
  curl -fsS -H 'X-Role: viewer' ':8000/compliance/report?format=pdf' > report_pro_run_1.pdf
  open report_pro_run_1.pdf
  ```

8) Export audit logs (optional)
The audit trail is useful for governance and incident review.
```zsh
curl -fsS -H 'X-Role: viewer' :8000/audit/logs | jq .
curl -fsS -H 'X-Role: viewer' :8000/audit/checksum | jq .
```

9) Teardown
```zsh
make demo-down
# or
docker compose -f deploy/docker-compose.yml down -v
```

Professional tips
- Start with `trimmed_mean`; switch to `krum` if you expect unreliable or adversarial updates.
- Track epsilon (ε) over time. Lower ε = stronger privacy; increase noise until utility is acceptable.
- Keep reports and audit logs with your model artifacts for reviews.
- Use unique `session_id`s for clear tracking across runs.

See also
- Quick Tour: `docs/basics/quick_tour.md`
- Beginner A–Z: `docs/basics/beginner_a_to_z.md`
- Train via API (detailed): `docs/technical/train_model.md`
- Compliance reports: `docs/technical/compliance_reports.md`
- Local Docker Compose: `docs/technical/local_docker_compose.md`
- Strategy guide: `docs/technical/federation_strategy_guide.md`
