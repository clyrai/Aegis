Docs QA checklist

Use this checklist before each release.

Required sections
- Home and Quick tour
- Getting started and Install & deploy
- Architecture and Operations
- API reference and Compliance reports
- Observability and Troubleshooting

Quality checks
- Build: `python -m mkdocs build --strict` succeeds.
- Links: No broken internal links or missing nav entries.
- Copy: Actionable, concise steps with copy‑paste commands.
- Security: mTLS/RBAC guidance present; secrets handling is explicit.
- Production: Rate limits, backups, and alerting documented.

Runbook excerpts
```zsh
make docs-up
open http://localhost:3000
curl -fsS -H 'X-Role: viewer' http://localhost:8000/compliance/report | head -n 20
```
