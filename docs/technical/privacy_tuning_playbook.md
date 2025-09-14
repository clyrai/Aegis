# Privacy tuning playbook

See also: Getting started (technical/getting_started.md) and Configuration matrix (technical/configuration_matrix.md).

Tools
- Prefer `httpie` + `jq` for readability, or use `curl`.
- Install on macOS: `brew install httpie jq`

Goals
- Find a privacy setting that protects individuals and keeps models useful.

Start here
- Begin with a balanced epsilon (e.g., noise_multiplier ≈ 1.0)
- Train a small number of rounds and check metrics

Tighten privacy
- Increase noise_multiplier or reduce sample_rate
- Watch accuracy and loss; expect some utility drop

Edge cases
- Tiny datasets: warn and consider aggregation or more rounds
- Highly imbalanced data: monitor minority-class metrics

Reporting
- Document chosen epsilon/delta and the observed tradeoffs

Copy‑paste examples
```zsh
# Balanced baseline
http POST :8000/dp/config \
	X-Role:operator \
	clipping_norm:=1.0 noise_multiplier:=1.0 sample_rate:=0.01 delta:=1e-5 accountant=rdp

# Stronger privacy (more noise)
http POST :8000/dp/config \
	X-Role:operator \
	clipping_norm:=1.0 noise_multiplier:=1.5 sample_rate:=0.005 delta:=1e-5 accountant=rdp

# Looser privacy (less noise) for utility validation
http POST :8000/dp/config \
	X-Role:operator \
	clipping_norm:=1.0 noise_multiplier:=0.7 sample_rate:=0.02 delta:=1e-5 accountant=rdp

# Start a short run and observe impact
http POST :8000/training/start X-Role:operator session_id=dp_tune rounds:=3
```

curl equivalents
```zsh
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
	-d '{"clipping_norm":1.0,"noise_multiplier":1.0,"sample_rate":0.01,"delta":1e-5,"accountant":"rdp"}' \
	http://localhost:8000/dp/config
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
	-d '{"clipping_norm":1.0,"noise_multiplier":1.5,"sample_rate":0.005,"delta":1e-5,"accountant":"rdp"}' \
	http://localhost:8000/dp/config
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
	-d '{"clipping_norm":1.0,"noise_multiplier":0.7,"sample_rate":0.02,"delta":1e-5,"accountant":"rdp"}' \
	http://localhost:8000/dp/config
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
	-d '{"session_id":"dp_tune","rounds":3}' http://localhost:8000/training/start
```
