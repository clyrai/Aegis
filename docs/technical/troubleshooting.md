# Troubleshooting

Can’t access services
- Check containers are healthy: `docker compose -f deploy/docker-compose.yml ps`
- Ports 8000/9090/3000 must be free

Grafana login fails
- Ensure `deploy/grafana/credentials/admin_password.txt` is set
- Restart Grafana: `docker compose -f deploy/docker-compose.yml up -d grafana`

Prometheus shows target down
- API must expose /metrics; check http://localhost:8000/metrics
- Network issues? Try `host.docker.internal:8000` on macOS

Training not progressing
- Reduce rounds; check participant registration and strategy
- Inspect API logs for validation errors
