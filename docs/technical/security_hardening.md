# Security hardening

Transport security (mTLS)
- Issue client/server certs from your CA; enforce client verification
- Rotate certs and pin CA bundles

Access control (RBAC)
- Admin: DP/FL config, start/stop training, reports
- Operator: run sessions with approved configs
- Viewer: read-only metrics and reports

Audit integrity
- Store logs in append-only storage; enable hashing/signing
- Alert on tampering attempts

Secrets
- Use mounted files or secret managers; never commit secrets to git

Copy‑paste snippets (dev)
```zsh
# Generate a local CA and server cert (dev only)
openssl req -x509 -newkey rsa:4096 -days 365 -nodes -subj "/CN=Aegis Dev CA" \
	-keyout dev-ca.key -out dev-ca.crt
openssl req -newkey rsa:4096 -nodes -subj "/CN=localhost" -keyout server.key -out server.csr
openssl x509 -req -in server.csr -CA dev-ca.crt -CAkey dev-ca.key -CAcreateserial -out server.crt -days 120

# Kubernetes secrets (example)
kubectl create secret tls aegis-tls --cert=server.crt --key=server.key -n aegis
kubectl create secret generic grafana-admin --from-literal=password='REPLACE_ME' -n aegis

# Docker Compose Grafana password file
mkdir -p deploy/grafana/credentials
print -r -- "$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 20)" > deploy/grafana/credentials/admin_password.txt
```
