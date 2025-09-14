---
title: Compliance reports
---

# Compliance reports

What’s included
- DP configuration: epsilon, delta, accountant method, clipping norm, noise multiplier, sample rate.
- Training audit: participants (counts), timestamps, strategy, versions.
- Regulatory mappings: GDPR, HIPAA, EU AI Act narratives; DPIA-style risk notes.

How to generate (Markdown)
```zsh
curl -fsS -H 'X-Role: viewer' http://localhost:8000/compliance/report | jq -r .markdown > report.md
```

How to generate (PDF)
```zsh
curl -fsS -H 'X-Role: viewer' 'http://localhost:8000/compliance/report?format=pdf' > report.pdf
```

PDF export
- Convert Markdown to PDF with your preferred tool (e.g., `pandoc` or CI pipeline step).

Best practices
- Include reports in model cards and governance packets.
- Keep alongside audit logs; ensure integrity and retention policies.
