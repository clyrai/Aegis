.PHONY: docs-up docs-down test-train demo-load prod-up prod-down demo-up demo-down oidc-up oidc-down ps logs

VENV=.venv

$(VENV):
	python3 -m venv $(VENV)
	. $(VENV)/bin/activate && python -m pip install -r requirements-dev.txt

# Start local stack
docs-up:
	sh -lc 'if docker compose version >/dev/null 2>&1; then docker compose -f deploy/docker-compose.yml up -d; else docker-compose -f deploy/docker-compose.yml up -d; fi'

# Stop local stack
docs-down:
	sh -lc 'if docker compose version >/dev/null 2>&1; then docker compose -f deploy/docker-compose.yml down -v; else docker-compose -f deploy/docker-compose.yml down -v; fi' || true

# Run the train_model smoke test against local
# Usage: make test-train [ROUNDS=5] [SESSION_ID=run1]
 test-train: docs-up
	BASE_URL=http://localhost:8000 \
	SESSION_ID=$${SESSION_ID:-run1} ROUNDS=$${ROUNDS:-5} \
	bash ./tests/docs/test_train_model.sh

# Generate demo load for Grafana recording
# Usage: make demo-load [DURATION=60] [BASE_URL=http://127.0.0.1:8000] [SESSION_ID=hipaa_run]
demo-load:
	bash ./scripts/demo_load.sh

# Production compose
prod-up:
	sh -lc 'if docker compose version >/dev/null 2>&1; then docker compose -f deploy/docker-compose.yml up -d; else docker-compose -f deploy/docker-compose.yml up -d; fi'

prod-down:
	sh -lc 'if docker compose version >/dev/null 2>&1; then docker compose -f deploy/docker-compose.yml down -v; else docker-compose -f deploy/docker-compose.yml down -v; fi' || true

# Demo override (disables rate limit, faster rounds)
demo-up:
	sh -lc 'if docker compose version >/dev/null 2>&1; then docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.demo.yml up -d aegis; else docker-compose -f deploy/docker-compose.yml -f deploy/docker-compose.demo.yml up -d aegis; fi'

demo-down:
	sh -lc 'if docker compose version >/dev/null 2>&1; then docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.demo.yml down; else docker-compose -f deploy/docker-compose.yml -f deploy/docker-compose.demo.yml down; fi' || true

# OIDC SSO (requires env vars or use oidc-test for Dex)
oidc-up:
	sh -lc 'if docker compose version >/dev/null 2>&1; then docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.oidc.yml up -d grafana; else docker-compose -f deploy/docker-compose.yml -f deploy/docker-compose.oidc.yml up -d grafana; fi'

oidc-down:
	sh -lc 'if docker compose version >/dev/null 2>&1; then docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.oidc.yml down; else docker-compose -f deploy/docker-compose.yml -f deploy/docker-compose.oidc.yml down; fi' || true

# Helpers
ps:
	sh -lc 'if docker compose version >/dev/null 2>&1; then docker compose -f deploy/docker-compose.yml ps; else docker-compose -f deploy/docker-compose.yml ps; fi'

logs:
	sh -lc 'docker logs --tail 200 aegis-grafana || true; docker logs --tail 200 aegis-prometheus || true; docker logs --tail 200 deploy-aegis-1 || true'
