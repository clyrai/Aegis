# Grafana Screenshots

Store sanitized screenshots used by the docs. Do not include secrets, hostnames, or user identifiers in captured images.

Required images referenced by docs (SVG placeholders included; you may replace with PNGs of the same base name):
- `overview.svg` — Aegis Overview top section (Requests, Error rate, RPS, Latency p95, Traffic)
- `latency.svg` — Latency p50/p95/p99 and endpoint breakdowns
- `health.svg` — Health panels (Target up, Scrape duration, RSS, CPU) and GC graph if available

Naming convention
- Use lowercase, hyphen-less nouns matching the section name
- Preferred: PNG format, max width ~1600px. For development, SVG placeholders are acceptable.

How to capture
1) Run the warmup script to create live metrics:
	```bash
	bash docs/tools/grafana_warmup.sh --duration 40
	```
2) Open Grafana (default http://localhost:3000), Dashboard: Aegis Overview
3) Set time range to `Last 30 minutes`, refresh every `5s`
4) Zoom/pan to show activity; crop to the required panels
5) Export as PNG or take a screenshot and save with the names above

Security tips
- Avoid showing container IDs, IPs, or internal domains
- Prefer generic time ranges and remove user avatars/names if visible
# Grafana screenshots

Store sanitized dashboard screenshots (no sensitive data). Suggested naming:
- `overview.png` — main training overview dashboard
- `epsilon.png` — epsilon consumption panel or dashboard
- `rounds.png` — rounds/ETA panel
- `clients.png` — client health/participation

Guidelines
- Capture from test/simulated runs to avoid real data exposure.
- Redact any identifiers not meant for sharing.
- Keep image sizes reasonable (< 500 KB if possible).
- Commit PNG or optimized WebP.
