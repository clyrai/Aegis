# Run locally with Docker Compose

This guide shows exactly how a user can run Aegis locally on macOS/Linux using Docker Compose, including both Compose V2 (`docker compose`) and legacy `docker-compose` commands. It also includes alternatives: running the published container directly (GHCR) and Kubernetes via Helm.

## Prerequisites
- Docker Desktop (macOS) or Docker Engine (Linux)
- Compose V2 plugin (`docker compose`) or legacy `docker-compose`
- `curl` and optionally `jq`

Check which compose you have:
```zsh
docker compose version || docker-compose version
```

## 1) Prepare Grafana admin password
Create the password file used by Grafana’s startup script:
```zsh
echo 'ChangeMe_StrongPassw0rd!' > deploy/grafana/credentials/admin_password.txt
```

## 2) Start the stack
Choose ONE of the following depending on your compose binary.

Compose V2 (preferred):
```zsh
docker compose -f deploy/docker-compose.yml up -d
```

Legacy docker-compose:
```zsh
docker-compose -f deploy/docker-compose.yml up -d
```

## 3) Verify services are healthy
```zsh
# API
curl -fsS http://localhost:8000/healthz

# Grafana
curl -fsS http://localhost:3000/api/health

# Prometheus
curl -fsS http://localhost:9090/-/ready
```
Expected outputs:
- API: `{ "status": "ok" }`
- Grafana: `{ "database": "ok", ... }`
- Prometheus: `Prometheus Server is Ready.`

Open dashboards:
```zsh
open http://localhost:3000
```

## 4) Run a short training session
Start a short run and then check status.
```zsh
# Start 10 rounds
curl -fsS -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-Role: admin' \
  http://localhost:8000/training/start \
  -d '{"session_id":"demo-quick","rounds":10}'

# Check progress
curl -fsS -H 'X-Role: viewer' \
  'http://localhost:8000/training/status?session_id=demo-quick' | jq .
```

## 5) Teardown
Compose V2:
```zsh
docker compose -f deploy/docker-compose.yml down -v
```

Legacy docker-compose:
```zsh
docker-compose -f deploy/docker-compose.yml down -v
```

## Troubleshooting
- `unknown command: docker compose` → use `docker-compose` or update Docker Desktop.
- Ports in use (8000/3000/9090) → stop other services or edit host ports in `deploy/docker-compose.yml`.
- Grafana login issues → ensure the password file exists before starting services.

---

## Alternative A: Single container (GHCR)
Use the published multi-arch container directly for quick API smoke tests.
```zsh
# Latest stable or pin to a version
docker pull ghcr.io/clyrai/aegis:v0.1.2

# Run API on :8000
docker run --rm -p 8000:8000 ghcr.io/clyrai/aegis:v0.1.2

# Health check
curl -fsS http://localhost:8000/healthz
```

Apple Silicon tip: Docker selects `arm64` automatically. To force:
```zsh
docker pull --platform linux/arm64 ghcr.io/clyrai/aegis:v0.1.2
```

## Alternative B: Kubernetes (Helm)
```zsh
helm install aegis deploy/helm/aegis -n aegis --create-namespace

# Later
helm uninstall aegis -n aegis
```
