# Technical Guide

Install (local)
- Requirements: Docker, docker compose, macOS/Linux
- Start services:
  - `docker compose -f deploy/docker-compose.yml up -d`
- Verify:
  - API: http://localhost:8000/healthz
  - Prometheus: http://localhost:9090/-/ready
  - Grafana: http://localhost:3000/api/health

Privacy configuration
- DP‑SGD: noise multiplier, clipping norm, sample rate
- Epsilon targeting with delta; step‑wise accounting
- Tune DP in examples or via API/CLI

Federated orchestration
- Flower strategy selection: Krum or Trimmed Mean
- Participant registration, auth, and health checks
- Retry/backoff for stragglers

Security and operations
- mTLS across services (docs include certs/runbook)
- RBAC roles: admin, operator, viewer
- Audit logs: structured JSON with event hashing

Compliance reporting
- Generate Markdown/PDF with DP config, training metadata, and regulatory mapping

Kubernetes (high‑level)
- Deploy manifests in `deploy/k8s/`
- Mount secrets for TLS and Grafana admin password
- Configure ingress and TLS termination per environment
