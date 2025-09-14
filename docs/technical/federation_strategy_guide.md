# Federation strategy guide

Related: Security model (features/security_model.md) and Observability & dashboards (technical/observability_and_dashboards.md).

Tools
- `httpie` and `jq` recommended. Install: `brew install httpie jq`

Trimmed Mean
- Best when you expect mild outliers; keeps central mass of updates
- Tunable trim percent; robust averages

Krum
- Best when a few clients may be adversarial or very noisy
- Selects updates closest to the majority; good Byzantine tolerance

Choosing quickly
- Unsure? Start with Trimmed Mean for general robustness
- Expect attackers or heavy noise? Use Krum

Copy‑paste examples
```zsh
# Select Trimmed Mean
http POST :8000/strategy X-Role:operator strategy=trimmed_mean

# Select Krum
http POST :8000/strategy X-Role:operator strategy=krum

# Start a 5‑round session with chosen strategy
http POST :8000/training/start X-Role:operator session_id=fed_test rounds:=5
```

curl equivalents
```zsh
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
	-d '{"strategy":"trimmed_mean"}' http://localhost:8000/strategy
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
	-d '{"strategy":"krum"}' http://localhost:8000/strategy
curl -fsS -H 'X-Role: operator' -H 'Content-Type: application/json' \
	-d '{"session_id":"fed_test","rounds":5}' http://localhost:8000/training/start
```
