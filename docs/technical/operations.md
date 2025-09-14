---
title: Operations
---

# Operations runbook

Day 2 operations
- TLS/mTLS: Issue short‑lived certs from your CA; require client certs for participants; rotate on a schedule.
- RBAC: Map `admin`, `operator`, `viewer` to IdP groups; prefer OIDC for Grafana; disable local admin.
- Secrets: Keep Grafana/admin creds and TLS keys in Secret stores; never commit; rotate and audit.
- Backups: Persist Prometheus/Grafana volumes; snapshot compliance reports and audit logs to immutable storage.
- Alerts: Error rate, latency p95, Prometheus targets down, disk usage, cert expiry.

Change management
- Pin dependencies; generate SBOM; scan images (Trivy); sign images (cosign); enforce in CI/CD before prod.
- Blue/green or canary deploys for API and coordinator.

Disaster recovery
- Backup cadence: daily config + weekly full; test restores quarterly.
- Restore order: Secrets, ConfigMaps, Prometheus/Grafana volumes, then API/Coordinator.

Certificates and rotation
- Maintain a CA; automate issuance via your PKI or cert-manager; document renewal windows.
- Monitor expiry and alert 14 days prior.

Audit and compliance
- Forward JSON audit logs to SIEM; enable immutability/versioning; include report artifacts in model governance packets.
