# Getting started (effective use)

Related: Privacy tuning playbook (technical/privacy_tuning_playbook.md), Federation strategies (technical/federation_strategy_guide.md), and API reference (technical/api_reference.md).

Before you begin
- Install Docker and docker compose
- Optional: set GRAFANA_ADMIN_USER and write Grafana password to deploy/grafana/credentials/admin_password.txt

Start the stack
- Start services:
	- `docker compose -f deploy/docker-compose.yml up -d`
- Open API docs: http://localhost:8000/docs
- Open Grafana: http://localhost:3000 (use the admin password at `deploy/grafana/credentials/admin_password.txt`)

Run a privacy‑preserving training
1) Register participants (or use simulated ones)
2) Pick a privacy level (epsilon); start with a balanced default
3) Start a federated session; monitor accuracy and privacy budget
4) Export a compliance report for stakeholders

Tips for success
- Start with higher epsilon (weaker privacy) to validate utility, then tighten
- Watch epsilon consumption and learning curves in Grafana
- Use Krum if you expect bad actors; Trimmed Mean for robust averages
- Keep audit logs; include report in review packets

What next
- See technical/guide.md for configuration details and Kubernetes pointers.
- Ready to train? See technical/train_model.md for a step‑by‑step walkthrough.
