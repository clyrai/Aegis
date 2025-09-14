# mTLS in Aegis (Operations)

Aegis API should be deployed with mutual TLS (mTLS) so only authenticated clients can connect.

## Local (Uvicorn/Gunicorn)

- Generate a CA, server cert/key, and client cert/key pairs.
- Run Uvicorn with SSL options and require client certs via reverse proxy (recommended) or `uvicorn --ssl-*` options in front of a TLS-terminating proxy that verifies client certs.

Example (behind nginx/haproxy/Envoy performing mTLS):
- Proxy terminates TLS, validates client cert against CA, and forwards only authenticated traffic to Uvicorn over localhost.
- Enforce a header such as `X-Client-Cert-Subject` for auditing (do not trust it from the public internet).

## Kubernetes

- Store CA, server key/cert, and (optionally) CRL in Secrets.
- Use an Ingress Controller (nginx, Istio, Envoy) to enforce `client-certificate: required` and mount CA bundle to verify clients.
- Short-lived client certs via your PKI/ACME with rotation (documented in cluster runbook).

## Server-side verification points

- Terminate TLS with client cert validation at the edge (Ingress/Proxy).
- Pass authenticated principal as a header to the app on loopback only.
- Use RBAC within app to enforce permissions and audit all actions.

## Errors & rotation

- On cert expiration or mismatch, return 4xx from proxy and log.
- Rotate CA/certs and restart rolling deployments; keep old CA in trust bundle during transition.
