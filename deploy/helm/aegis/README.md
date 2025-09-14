# Aegis Helm Chart

Quick start:

- Dry-run render:
  helm template aegis ./deploy/helm/aegis

- Lint:
  helm lint ./deploy/helm/aegis

- Install:
  helm install aegis ./deploy/helm/aegis \
    --set image.repository=clyrai/aegis \
    --set image.tag=dev

Values of note:
- mtls.enabled: true to mount TLS cert secret (aegis-tls)
- service.port: Service port to expose internally
- resources: CPU/memory requests/limits
