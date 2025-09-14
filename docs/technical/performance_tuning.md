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
# Run with more rounds
http POST :8000/training/start X-Role:operator session_id=perf1 rounds:=10

# Measure server CPU/mem (macOS)
top -l 1 | head -n 15

# Prometheus scrape duration (approx via UI) or query with API
curl -fsS 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.9%2C%20sum(rate(prometheus_tsdb_wal_fsync_duration_seconds_bucket%5B5m%5D))%20by%20(le))' | jq .status
```

Note: Some performance levers (batch size, LR, participants per round) are model‑specific and controlled in client code or orchestration settings not covered here. The snippet above focuses on server‑side knobs available in this API.
