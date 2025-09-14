# Performance tuning

Levers
- Batch size and learning rate
- Number of rounds and participants per round
- Aggregation strategy overhead (Krum > Trimmed Mean)

Guidelines
- Start small; scale rounds/participants as metrics stabilize
- Monitor CPU/memory, scrape durations, and training time per round

Scaling
- Horizontal: more participants
- Vertical: larger instances for heavy models

Copy‑paste experiments
```zsh
# Try larger batch size via model config (example endpoint)
http POST :8000/model/config X-Role:operator batch_size:=128 lr:=0.01

# Run with more rounds and participants per round
http POST :8000/training/start X-Role:operator session_id=perf1 rounds:=10 ppr:=4

# Measure server CPU/mem (macOS)
top -l 1 | head -n 15

# Prometheus scrape duration (approx via UI) or query with API
curl -fsS 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.9%2C%20sum(rate(prometheus_tsdb_wal_fsync_duration_seconds_bucket%5B5m%5D))%20by%20(le))' | jq .status
```
