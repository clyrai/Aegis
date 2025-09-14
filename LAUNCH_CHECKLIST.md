Launch checklist

This checklist verifies Aegis is ready to demo or deploy. All commands assume macOS with zsh.

1) Start the stack

```zsh
make prod-up

make demo-up

make oidc-up
```

2) Quick health checks

```zsh
curl -fsS http://localhost:8000/healthz | jq .
curl -fsS -H 'X-Role: viewer' http://localhost:8000/compliance/report | head -n 20
curl -fsS http://localhost:9090/-/ready
curl -fsS http://localhost:3000/api/health | jq .
```

3) Start a training session and watch status

```zsh
curl -fsS -X POST -H 'Content-Type: application/json' -H 'X-Role: admin' \
  http://localhost:8000/training/start \
  -d '{"session_id":"demo","rounds":2000}'

curl -fsS -H 'X-Role: viewer' 'http://localhost:8000/training/status?session_id=demo' | jq .
```

4) Open dashboards

```zsh
open http://localhost:3000/d/aegis-overview/aegis-overview
```

5) Grafana credentials

- User: `admin` (override via `GRAFANA_ADMIN_USER`)
- Password: contents of `deploy/grafana/credentials/admin_password.txt`

Search provisioned dashboards via API:
```zsh
PASS=$(cat deploy/grafana/credentials/admin_password.txt)
USER=${GRAFANA_ADMIN_USER:-admin}
curl -fsS -u "$USER:$PASS" 'http://localhost:3000/api/search?query=aegis' | jq -r '.[].title'
```

6) Prometheus targets sanity

```zsh
curl -fsS http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | [.labels.job, .labels.instance, .health] | @tsv'
```

7) Teardown

```zsh
make prod-down    # or: make demo-down
```

Troubleshooting

- If Grafana search via shell fails due to URL globbing, wrap the URL in single quotes.
- If `jq` is not installed, omit `| jq …` or install via `brew install jq`.
- Confirm containers are up:
```zsh
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
```

Security notes (production)

- Use mTLS between services and external clients where applicable.
- Rotate Grafana admin password and configure OIDC (`deploy/docker-compose.oidc.yml`).
- Set RBAC-aware headers when calling the API (`X-Role: admin|operator|viewer`).
