Next-version backlog (vNext)

Purpose: Prioritize post-launch hardening and enhancements. All items are non-breaking and can be delivered incrementally.

1) Security & compliance hardening
- Grafana SSO only: enable OIDC by default and disable local admin after verification.
  - Acceptance: Login only via IdP; local admin disabled; runbook updated.
- API auth: enforce JWT/OIDC at the edge; optional OPA policy checks.
  - Acceptance: Requests require valid token; RBAC mapped to IdP groups; policy sample provided.
- mTLS enforcement presets: sample configs + cert-manager automation guide.
  - Acceptance: Working reference manifests and rotation runbook.
- Edge protection: WAF + rate limiting presets.
  - Acceptance: Example reverse-proxy config and test cases for abuse scenarios.

2) CI/CD and supply chain
- Container scanning (Trivy) in CI; fail on High/Critical.
- Image signing (cosign) and verification step before deploy.
- SBOM generation (Syft) and publication as artifact.
- Docs CI: mkdocs build + link check; optional publish to Pages.
  - Acceptance: CI workflow green; artifacts visible; signed images gated for prod.

3) Observability & alerts
- Alert rules: error rate, latency p95, target down, disk usage, cert expiry.
- Dashboard polish: epsilon consumption over time; federated client health; DP budget burn-down.
- Log shipping: audit logs to SIEM with integrity hints.
  - Acceptance: Alerts fire in dev; dashboards show new panels; SIEM receives logs.

4) Documentation
- Link current orphan pages (Brand assets, Grafana assets, Playbooks README).
- Security deep-dive diagram with trust boundaries per endpoint.
- Upgrade guide and breaking-change policy.
  - Acceptance: mkdocs strict build remains green; user can perform upgrade using guide.

5) Product features
- Robust aggregators: add coordinate-wise median and Bulyan options.
- Secure aggregation (optional module) design stub.
- Policy presets: HIPAA/GDPR/PCI parameter templates (epsilon/delta/noise/clip) with rationale.
  - Acceptance: Example runs complete with presets; docs include policy tables.

6) Testing & resilience
- Load tests for concurrent sessions and large models; baseline metrics recorded.
- Network chaos tests: participant flaps, partitions, retries.
- Advanced privacy attacks: shadow-model MI, gradient inversion variants across epsilon grid.
- Long-run stability: 24h soak; memory leak and file descriptor checks.
  - Acceptance: Tests automated; reports in test_results/; documented thresholds.

Notes
- Keep changes backward compatible; feature-flag anything risky.
- Update DOCS_CHECKLIST.md and LAUNCH_CHECKLIST.md if workflows change.
