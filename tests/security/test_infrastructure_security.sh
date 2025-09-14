#!/usr/bin/env bash
set -euo pipefail

echo "[Security] Infrastructure security tests"

ROOT_DIR=$(cd "$(dirname "$0")"/../.. && pwd)
RESULTS_DIR="$ROOT_DIR/test_results"
mkdir -p "$RESULTS_DIR"

echo "[Security] Running RBAC and mTLS (sim) negative tests via pytest"
pytest -q tests/test_api_security.py tests/test_api_mtls.py \
	>"$RESULTS_DIR/security_infrastructure.log" 2>&1 || {
	echo "[Security] RBAC/mTLS checks failed (see test_results/security_infrastructure.log)"; exit 1; }

echo "[Security] OK"
