---
title: Change Grafana credentials
---

# Change Grafana credentials

Prefer SSO (OIDC) in production and disable local admin after verification. For local/dev, use the methods below.

Docker Compose (local/dev)
1) Set the admin username (optional) and password file:
   - Username: env var `GRAFANA_ADMIN_USER` (defaults to `admin`).
   - Password: write the new password to `deploy/grafana/credentials/admin_password.txt`.
2) Restart Grafana so the entrypoint resets the password:
```zsh
make prod-up   # or: docker compose -f deploy/docker-compose.yml up -d
```
Notes
- The compose file mounts the password as a Docker Secret and uses `grafana cli admin reset-admin-password` at startup.
- To rotate, update the file, then restart the Grafana container.

CLI (inside container)
```zsh
docker exec -it aegis-grafana grafana cli admin reset-admin-password 'NEW_PASSWORD'
```

Kubernetes (production)
1) Store credentials in a Secret:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: grafana-admin
type: Opaque
stringData:
  admin-user: admin
  admin-password: "S3cure-ChangeMe"
```
2) Mount via env and configure chart/deployment to use them:
```yaml
env:
  - name: GF_SECURITY_ADMIN_USER
    valueFrom:
      secretKeyRef:
        name: grafana-admin
        key: admin-user
  - name: GF_SECURITY_ADMIN_PASSWORD
    valueFrom:
      secretKeyRef:
        name: grafana-admin
        key: admin-password
```
3) Rotate by updating the Secret and rolling the Deployment:
```zsh
kubectl create secret generic grafana-admin \
  --from-literal=admin-user=admin \
  --from-literal=admin-password='NEW_PASSWORD' \
  -o yaml --dry-run=client | kubectl apply -f -
kubectl rollout restart deploy/grafana
```

OIDC SSO (recommended)
- Use `deploy/docker-compose.oidc.yml` to enable OIDC locally for testing.
- In production, configure Grafana with your IdP; restrict local login and disable built-in admin after verifying SSO works.

Security tips
- Never commit passwords to git; use Docker/K8s Secrets.
- Rotate regularly; prefer short-lived SSO tokens over static passwords.
