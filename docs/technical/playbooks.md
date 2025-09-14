# Production Playbooks (Industry Scripts)

Turn-key, production-minded scripts for common regulated industries. They use the same Aegis API you’ve seen in the training guide, but with sensible defaults per domain.

Step-by-step workflow
1) Step 1 — Bring up the stack
	```zsh
	make docs-up
	# or
	docker compose up -d
	```
	Components started: API (FastAPI), Federated Coordinator (Flower), Prometheus, Grafana.

2) Step 2 — Configure environment (optional)
	```zsh
	export BASE_URL=http://localhost:8000
	export ROUNDS=8 STRATEGY=trimmed_mean
	export CLIP=1.0 NOISE=1.0 SAMPLE_RATE=0.01 DELTA=1e-6 ACCOUNTANT=rdp
	# TLS/mTLS
	export CLIENT_CERT=~/.certs/client.crt CLIENT_KEY=~/.certs/client.key CA_CERT=~/.certs/ca.pem
	export TIMEOUT=15 RETRIES=45
	```

3) Step 3 — Run a playbook script
	```zsh
	bash docs/playbooks/healthcare_hipaa.sh   # HIPAA-leaning defaults, Krum
	bash docs/playbooks/finance_pci.sh        # PCI-leaning defaults
	bash docs/playbooks/retail_gdpr.sh        # GDPR-leaning defaults
	```
	Outputs: compliance report Markdown under `test_artifacts/` (configurable via `ARTIFACT_DIR`).

4) Step 4 — Monitor in Grafana
	- URL: `http://localhost:3000`
	- Use the Observability guide for dashboards and metrics: `technical/observability_and_dashboards.md`
	- Suggested panels: training rounds, per-round accuracy/loss, epsilon estimate, client participation/health.
	- Filter by `session_id` (visible in script logs).

5) Step 5 — Review compliance artifacts
	- File: `test_artifacts/report_<SESSION_ID>.md`
	- Endpoints: `/compliance/report`, `/compliance/hipaa`, `/compliance/gdpr`.

What’s inside each script
- Participant registration with deterministic client keys (sample)
- DP configuration tuned for each domain (clip, noise, sample_rate, delta, accountant)
- Aggregator selection (Krum or Trimmed Mean)
- Training lifecycle (start + polling) with round/epsilon/ETA display
- Compliance report written to `test_artifacts/`
  - Integrates `/compliance/report` and can be paired with `/compliance/hipaa` or `/compliance/gdpr` checks

Customize via env vars (examples)
```zsh
ROUNDS=10 STRATEGY=krum NOISE=1.5 bash docs/playbooks/healthcare_hipaa.sh
BASE_URL=https://aegis.company.internal:8000 bash docs/playbooks/finance_pci.sh
ARTIFACT_DIR=./reports bash docs/playbooks/retail_gdpr.sh
CLIENT_CERT=~/.certs/client.crt CLIENT_KEY=~/.certs/client.key CA_CERT=~/.certs/ca.pem bash docs/playbooks/healthcare_hipaa.sh
```

Production reminders
- Enable mTLS and RBAC in your deployment; these scripts assume local dev headers.
- Store audit logs and compliance reports in a secure, immutable store.
- Review DP choices with your privacy/compliance team (epsilon/delta targets).
- Configure timeouts/retries for your networking environment (`TIMEOUT`, `RETRIES`, `RETRY_DELAY`).

Related docs
- Orchestration walkthrough: `technical/train_model.md`
- DP tuning: `technical/privacy_tuning_playbook.md`
- Federation strategies: `technical/federation_strategy_guide.md`
- Observability & dashboards: `technical/observability_and_dashboards.md`
