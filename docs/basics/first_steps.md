# Start here: What is Aegis?

Plain words, no buzzwords:
- Aegis lets you train ML models without pooling raw data in one place.
- It protects people’s privacy automatically while training.
- It gives you simple controls, clear reports, and production‑ready ops.

Key ideas (kept simple)
- Differential Privacy (DP): adds a tiny amount of noise so individual records can’t be picked out.
- Federated Learning (FL): each site trains locally; only model updates are shared.
- Guardrails: permissions (RBAC), encrypted connections (mTLS), and audit logs.

Is Aegis for me?
- You work with sensitive data (healthcare, finance, public sector, education).
- You need to collaborate across multiple sites or companies.
- You must explain privacy protections to non‑technical stakeholders.

What you get on day one
- One command to start a demo with dashboards
- Easy privacy settings (pick a privacy level, we do the math)
- Built‑in federated training that tolerates slow or unreliable sites
- Click‑to‑generate reports for compliance reviews

Quick start (5–10 min)
1) Start locally: see docs/scripts/start_local.sh
2) Open the API docs at http://localhost:8000/docs
3) Start a federated run with a balanced privacy setting
4) Watch Grafana at http://localhost:3000, then export a report

Next steps
- New to terms? See basics/glossary.md
- Curious about value? See features/overview.md
