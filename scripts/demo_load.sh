#!/usr/bin/env bash
set -euo pipefail

# Aegis demo load generator for Grafana recording
# - Ramps concurrency and mixes endpoints for a visually rich dashboard
# - Default duration ~60s; tweak via env vars
#
# Env:
#   BASE_URL (default: http://127.0.0.1:8000)
#   DURATION (total seconds, default: 60)
#   SESSION_ID (default: hipaa_run)

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
DURATION=${DURATION:-60}
SESSION_ID="${SESSION_ID:-hipaa_run}"

end=$((SECONDS + DURATION))

echo "Demo load: BASE_URL=${BASE_URL} DURATION=${DURATION}s SESSION_ID=${SESSION_ID}"

phase() {
  local conc=$1 dur=$2
  echo "Phase: ${conc} workers for ${dur}s"
  for w in $(seq 1 "$conc"); do
    (
      pend=$((SECONDS + dur))
      while [ $SECONDS -lt $pend ]; do
        r=$((RANDOM % 100))
        if [ $r -lt 5 ]; then
          curl -fsS -m 4 -H 'X-Role: viewer' "${BASE_URL}/compliance/report" > /dev/null || true
        elif [ $r -lt 30 ]; then
          curl -fsS -m 2 -H 'X-Role: viewer' "${BASE_URL}/training/status?session_id=${SESSION_ID}" > /dev/null || true
        elif [ $r -lt 50 ]; then
          curl -fsS -m 2 "${BASE_URL}/metrics" > /dev/null || true
        else
          curl -fsS -m 2 "${BASE_URL}/healthz" > /dev/null || true
        fi
      done
    ) &
  done
  wait
}

# Three phases: gentle -> moderate -> heavy
phase 20 15
phase 50 15
phase 100 $(( DURATION - 30 ))

echo "Demo load complete."
