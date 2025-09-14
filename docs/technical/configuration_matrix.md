# Configuration matrix (quick reference)

Differential Privacy
- clipping_norm: float (0.1–10), default 1.0
- noise_multiplier: float (0.5–3.0), default 1.0
- sample_rate: float (0.001–0.5), default 0.01
- delta: float (<= 1e-3), default 1e-5
- accountant: rdp | gaussian | moments

Federation
- strategy: krum | trimmed_mean
- rounds: int (1–1000)
- participants_per_round: auto | N
- retry_backoff: seconds

Security
- mTLS: enabled | disabled (prod: enabled)
- RBAC roles: admin | operator | viewer
- audit: JSONL | SQLite+HMAC

Observability
- Prometheus: scrape_interval (default 5s)
- Grafana: admin user; password via file secret

Copy‑paste presets
```zsh
# Conservative privacy preset
http POST :8000/dp/config X-Role:operator clipping_norm:=0.5 noise_multiplier:=2.0 sample_rate:=0.005 delta:=1e-5 accountant=rdp

# Balanced privacy preset
http POST :8000/dp/config X-Role:operator clipping_norm:=1.0 noise_multiplier:=1.0 sample_rate:=0.01 delta:=1e-5 accountant=rdp

# Robust aggregation preset (Trimmed Mean 10%)
http POST :8000/strategy X-Role:operator strategy=trimmed_mean

# Byzantine tolerance preset (Krum, m=2)
http POST :8000/strategy X-Role:operator strategy=krum
```

curl equivalents
```zsh
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
	-d '{"clipping_norm":0.5,"noise_multiplier":2.0,"sample_rate":0.005,"delta":1e-5,"accountant":"rdp"}' http://localhost:8000/dp/config
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
	-d '{"clipping_norm":1.0,"noise_multiplier":1.0,"sample_rate":0.01,"delta":1e-5,"accountant":"rdp"}' http://localhost:8000/dp/config
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
	-d '{"strategy":"trimmed_mean"}' http://localhost:8000/strategy
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
	-d '{"strategy":"krum"}' http://localhost:8000/strategy
```
