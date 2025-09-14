Production runbook

- Container hardening:
  - Non-root user (UID 10001), read-only root FS, no extra capabilities.
  - Gunicorn with Uvicorn workers, healthcheck on /healthz.
  - Minimal build context via .dockerignore, multi-stage build to reduce size.
- Docker compose:
  - Override host port via AEGIS_HOST_PORT, healthcheck without curl dependency.
- Kubernetes:
  - SecurityContext enforcing non-root, drop ALL caps, readOnlyRootFilesystem.
  - Resource requests/limits and HTTP probes.
  - Provide TLS secrets in aegis-tls; mount at /etc/aegis/certs if using mTLS.
- CI/CD:
  - Ensure image is built with immutable tags and signed (e.g., cosign) before promotion.
  - Run ruff, mypy, pytest in CI (already configured), plus container scan (Trivy) recommended.

Quick start

- Build and run local container:
  docker-compose up -d --build

- k8s dry-run (no cluster fallback supported):
  bash deploy/validate_k8s.sh

Promote to prod

- Bake image with pinned dependencies and sign the digest.
- Apply k8s manifests with proper TLS secrets populated and an Ingress/Service configured as per your platform.

License: Apache-2.0. See `LICENSE` for full terms.