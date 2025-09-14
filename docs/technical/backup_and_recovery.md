# Backup & recovery

What to back up
- Compliance reports and audit logs
- Model checkpoints and run metadata
- Config files and certificates (never commit private keys)

Strategy
- Daily encrypted backups with retention policy
- Test restore quarterly
- Store CA root offline; rotate leaf certs regularly

Disaster recovery
- Document RPO/RTO targets
- Automate compose/k8s redeploy from backups

Copy‑paste examples
```zsh
# Local backup (compose volumes)
tar czf backups/aegis-$(date +%F).tgz \
	deploy/prometheus/prometheus.yml \
	deploy/grafana/aegis_dashboard.json \
	deploy/grafana/credentials/admin_password.txt || true

# Kubernetes: export manifests and secrets (namespaced)
kubectl get all,cm,secret -n aegis -o yaml > backups/aegis-k8s-$(date +%F).yaml

# Restore (compose): redeploy
docker compose -f deploy/docker-compose.yml down -v
docker compose -f deploy/docker-compose.yml up -d

# Offsite copy (placeholder: replace with your S3 bucket)
aws s3 cp backups/aegis-$(date +%F).tgz s3://YOUR-BUCKET/aegis/
```

Tools
- Install AWS CLI and jq if needed:
	```zsh
	brew install awscli jq
	```
