# Install and deploy

## Local (Docker Compose)

Requirements
- Docker and docker compose
- Set Grafana admin password file: write a strong password to `deploy/grafana/credentials/admin_password.txt`

Start services
```bash
docker compose -f deploy/docker-compose.yml up -d
```

Verify
- API: `http://localhost:8000/healthz`
- Prometheus: `http://localhost:9090/-/ready`
- Grafana: `http://localhost:3000/api/health`

Stop services
```bash
docker compose -f deploy/docker-compose.yml down -v
```

## Production (Kubernetes)

Option A: Apply manifests
```bash
kubectl apply -f deploy/k8s/secrets.yaml
kubectl apply -f deploy/k8s/configmap.yaml
kubectl apply -f deploy/k8s/deployment.yaml
kubectl apply -f deploy/k8s/service.yaml
```

Option B: Helm chart (customize `deploy/helm/aegis/values.yaml`)
```bash
helm install aegis deploy/helm/aegis -n aegis --create-namespace
```

Ingress and TLS
- Terminate TLS at Ingress (or use passthrough) and enforce security headers
- For mTLS with participants, issue client certs from your CA and require verification

RBAC and audit
- Map roles (admin/operator/viewer) to your IdP groups
- Persist audit logs; set retention and integrity (hashing/signing)

## Secrets

- Grafana admin password: mount from Secret as file; username via env
- TLS certs/keys: store as Secrets; rotate regularly
- Never commit secrets to git; prefer external secret managers in production
