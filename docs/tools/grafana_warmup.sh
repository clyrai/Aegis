#!/usr/bin/env bash
set -euo pipefail

# Grafana Warmup Script
# Purpose: Generate lively API and training traffic so dashboards look active.
# - Starts HIPAA, PCI, and GDPR playbooks with short runs (default 6 rounds each)
# - Continuously hits /training/status, /compliance/report, and /metrics
# - Optionally injects a few 4xx requests to light up error panels

command -v curl >/dev/null 2>&1 || { echo "curl is required"; exit 1; }

DURATION=40
INJECT_ERRORS=1
ROUNDS=${ROUNDS:-6}
BASE_URL=${BASE_URL:-http://localhost:8000}

usage() {
  cat <<USAGE
Usage: $0 [--duration SECONDS] [--no-errors]
Env: BASE_URL (default $BASE_URL), ROUNDS (default $ROUNDS)
USAGE
}

while [[ ${1:-} =~ ^- ]]; do
  case "$1" in
    --duration) shift; DURATION=${1:-40} ;;
    --no-errors) INJECT_ERRORS=0 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 2 ;;
  esac
  shift || true
done

echo "[warmup] BASE_URL=$BASE_URL DURATION=${DURATION}s ROUNDS=$ROUNDS"

echo "[warmup] Checking API readiness..."
for i in {1..20}; do
  if curl -fsS -m 3 "$BASE_URL/compliance/report" >/dev/null 2>&1; then
    echo "[warmup] API is reachable."
    break
  fi
  sleep 1
done

S1="hipaa_$(date +%H%M%S)"
S2="pci_$(date +%H%M%S)"
S3="gdpr_$(date +%H%M%S)"

mkdir -p test_artifacts

echo "[warmup] Starting playbooks: $S1 $S2 $S3"
(
  SESSION_ID="$S1" ROUNDS=$ROUNDS STRATEGY=krum bash docs/playbooks/healthcare_hipaa.sh > "test_artifacts/${S1}.log" 2>&1 || true &
  SESSION_ID="$S2" ROUNDS=$ROUNDS STRATEGY=trimmed_mean bash docs/playbooks/finance_pci.sh > "test_artifacts/${S2}.log" 2>&1 || true &
  SESSION_ID="$S3" ROUNDS=$ROUNDS STRATEGY=trimmed_mean bash docs/playbooks/retail_gdpr.sh > "test_artifacts/${S3}.log" 2>&1 || true &
) &

# Background traffic loops
pids=()

status_loop() {
  local sid="$1"
  while true; do
    curl -fsS -m 2 -H 'X-Role: viewer' "$BASE_URL/training/status?session_id=$sid" >/dev/null || true
    sleep 0.5
  done
}

report_loop() {
  while true; do
    curl -fsS -m 2 -H 'X-Role: viewer' "$BASE_URL/compliance/report" >/dev/null || true
    sleep 2
  done
}

metrics_loop() {
  while true; do
    curl -fsS -m 2 "$BASE_URL/metrics" >/dev/null || true
    sleep 1
  done
}

status_loop "$S1" & pids+=("$!")
status_loop "$S2" & pids+=("$!")
status_loop "$S3" & pids+=("$!")
report_loop & pids+=("$!")
metrics_loop & pids+=("$!")

if [[ "$INJECT_ERRORS" -eq 1 ]]; then
  echo "[warmup] Injecting a few 4xx requests to activate error panels"
  for i in {1..20}; do
    curl -s -o /dev/null -w '%{http_code}\n' "$BASE_URL/does-not-exist" || true
    sleep 0.2
  done
fi

cleanup() {
  echo "[warmup] Stopping background traffic..."
  for p in "${pids[@]}"; do
    kill "$p" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

echo "[warmup] Warming dashboards for ${DURATION}s ..."
sleep "$DURATION"
echo "[warmup] Done. You can now capture screenshots in Grafana."
