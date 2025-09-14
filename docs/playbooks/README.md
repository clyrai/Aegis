# Industry Playbooks (Production Scripts)

This folder provides production-ready, documented shell scripts tailored for industry scenarios. They exercise Aegis features end-to-end: participant registration, DP configuration, federated strategy selection, training lifecycle, and compliance reporting.

Available playbooks
- Healthcare (HIPAA): `healthcare_hipaa.sh`
- Finance (PCI): `finance_pci.sh`
- Retail (GDPR): `retail_gdpr.sh`

Step-by-step (script + docs)
1) Step 1 — Start the Aegis stack
	- Purpose: Bring up API, coordinator, Prometheus, and Grafana locally.
	- Command:
	```zsh
	make docs-up
	# or, if you prefer docker compose directly
	docker compose up -d
	```

2) Step 2 — (Optional) Set environment and security options
	- Purpose: Point to your API, enable TLS/mTLS, and tune DP/FL parameters.
	- Common variables to export in your shell:
	```zsh
	export BASE_URL=https://aegis.internal:8443
	export CLIENT_CERT=~/.certs/client.crt
	export CLIENT_KEY=~/.certs/client.key
	export CA_CERT=~/.certs/ca.pem
	export TIMEOUT=20 RETRIES=60
	# DP/FL tuning
	export ROUNDS=8 STRATEGY=krum NOISE=1.2 CLIP=1.0 SAMPLE_RATE=0.01 DELTA=1e-6 ACCOUNTANT=rdp
	```

3) Step 3 — Run a playbook
	- Purpose: Execute an end-to-end regulated workflow with sensible defaults per industry.
	- Commands (choose one):
	```zsh
	bash docs/playbooks/healthcare_hipaa.sh   # HIPAA-leaning defaults
	bash docs/playbooks/finance_pci.sh        # PCI-leaning defaults
	bash docs/playbooks/retail_gdpr.sh        # GDPR-leaning defaults
	```
	- Output: A compliance report Markdown file under `test_artifacts/` (or `ARTIFACT_DIR`).

4) Step 4 — Monitor training in Grafana
	- Purpose: Observe rounds, client health, DP epsilon consumption, and loss/accuracy.
	- Open Grafana (default): `http://localhost:3000` (credentials per your deploy; dev often `admin/admin`).
	- Dashboards: See the Observability guide for built-in dashboards and panels.
	  - Link: `technical/observability_and_dashboards.md`
	- Tip: Filter by `session_id` (from the script output) to isolate a specific run.

5) Step 5 — Review compliance report
	- Purpose: Share audit-ready evidence with compliance or risk teams.
	- The script writes: `test_artifacts/report_<SESSION_ID>.md` containing DP config, strategy, and audit summary.
	- See also API endpoints `/compliance/report`, `/compliance/hipaa`, `/compliance/gdpr` for programmatic checks.

6) Step 6 — (Optional) Tear down
	```zsh
	docker compose down
	```

Environment variables
- `BASE_URL` (default `http://localhost:8000`) — API endpoint
- `SESSION_ID` (default auto) — training session name
- `ROUNDS` — number of federated rounds
- `STRATEGY` — `krum` or `trimmed_mean`
- `CLIP`, `NOISE`, `SAMPLE_RATE`, `DELTA`, `ACCOUNTANT` — DP knobs
- `ARTIFACT_DIR` — output reports directory (default `test_artifacts`)
- `TIMEOUT` — per-request timeout seconds (default `10`)
- `RETRIES`, `RETRY_DELAY` — API readiness wait (defaults `30`, `1`)
- `INSECURE` — set to any value to allow insecure TLS (`curl -k`)
- `CLIENT_CERT`, `CLIENT_KEY` — client mTLS cert/key paths
- `CA_CERT` — custom CA bundle path
- `CURL_EXTRA_ARGS` — extra flags passed to curl

Security notes
- In production, enable mTLS and proper RBAC roles; these scripts assume local dev defaults.
- Rotate keys, keep audit logs, and store compliance reports in a secure location.

Examples
```zsh
# Point to a remote API with mTLS and longer timeouts
BASE_URL=https://aegis.internal:8443 \
CLIENT_CERT=~/.certs/client.crt CLIENT_KEY=~/.certs/client.key CA_CERT=~/.certs/ca.pem \
TIMEOUT=20 RETRIES=60 bash docs/playbooks/healthcare_hipaa.sh

# Run PCI playbook with Krum and stricter DP noise
STRATEGY=krum NOISE=1.2 bash docs/playbooks/finance_pci.sh
```
