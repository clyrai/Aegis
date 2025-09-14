#!/usr/bin/env bash
set -euo pipefail

# Aegis Healthcare (HIPAA) Federated DP Training Script
# - Registers participants
# - Applies HIPAA-appropriate DP defaults (conservative)
# - Selects a robust aggregator (Krum)
# - Starts training and polls until completion
# - Generates a compliance report

# Requirements: curl, jq
command -v curl >/dev/null 2>&1 || { echo "curl is required"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "jq is required"; exit 1; }

BASE_URL=${BASE_URL:-http://localhost:8000}
SESSION_ID=${SESSION_ID:-hipaa_run_$(date +%s)}
ROUNDS=${ROUNDS:-5}
STRATEGY=${STRATEGY:-krum}

# HIPAA-leaning DP defaults (adjust per risk appetite)
CLIP=${CLIP:-1.0}
NOISE=${NOISE:-1.2}
SAMPLE_RATE=${SAMPLE_RATE:-0.01}
DELTA=${DELTA:-1e-5}
ACCOUNTANT=${ACCOUNTANT:-rdp}

ARTIFACT_DIR=${ARTIFACT_DIR:-test_artifacts}
GRAFANA_URL=${GRAFANA_URL:-http://localhost:3000}
mkdir -p "$ARTIFACT_DIR"

log() { printf "[%s] %s\n" "$(date -Iseconds)" "$*"; }

# Optional TLS / networking controls
TIMEOUT=${TIMEOUT:-10}
RETRIES=${RETRIES:-30}
RETRY_DELAY=${RETRY_DELAY:-1}
INSECURE=${INSECURE:-}
CLIENT_CERT=${CLIENT_CERT:-}
CLIENT_KEY=${CLIENT_KEY:-}
CA_CERT=${CA_CERT:-}
CURL_EXTRA_ARGS=${CURL_EXTRA_ARGS:-}

build_curl_opts() {
  local -a opts=()
  [[ -n "$INSECURE" ]] && opts+=( -k )
  [[ -n "$CLIENT_CERT" ]] && opts+=( --cert "$CLIENT_CERT" )
  [[ -n "$CLIENT_KEY" ]] && opts+=( --key "$CLIENT_KEY" )
  [[ -n "$CA_CERT" ]] && opts+=( --cacert "$CA_CERT" )
  if [[ -n "$CURL_EXTRA_ARGS" ]]; then
    # shellcheck disable=SC2206
    opts+=( $CURL_EXTRA_ARGS )
  fi
  if ((${#opts[@]})); then
    printf '%s\n' "${opts[@]}"
  fi
}
curl_exec() {
  if ((${#CURLOPTS[@]})); then
    curl "$@" "${CURLOPTS[@]}"
  else
    curl "$@"
  fi
}
declare -a CURLOPTS=()
CURLOPTS=( $(build_curl_opts) )

post_json() {
  local path=$1
  local role=$2
  local data=$3
  curl_exec -fsS -m "$TIMEOUT" -H "X-Role: ${role}" -H 'Content-Type: application/json' \
    -d "${data}" "${BASE_URL}${path}"
}

get_json() {
  local path=$1
  local role=$2
  curl_exec -fsS -m "$TIMEOUT" -H "X-Role: ${role}" "${BASE_URL}${path}"
}

wait_for_api() {
  log "Waiting for API at ${BASE_URL} ..."
  for i in $(seq 1 "$RETRIES"); do
    if curl_exec -fsS -m 5 -H 'X-Role: viewer' "${BASE_URL}/compliance/report" >/dev/null 2>&1; then
      log "API is reachable."
      return 0
    fi
    sleep "$RETRY_DELAY"
  done
  log "ERROR: API not reachable at ${BASE_URL} after ${RETRIES} attempts"
  exit 1
}

log "Step 1 — Check API readiness"
wait_for_api

log "Step 2 — Register participants (c1, c2)"
post_json /participants admin '{"client_id":"c1","key_hex":"aa"}' | jq .
post_json /participants admin '{"client_id":"c2","key_hex":"bb"}' | jq .

log "Step 3 — Configure DP (clip=${CLIP}, noise=${NOISE}, sample_rate=${SAMPLE_RATE}, delta=${DELTA}, accountant=${ACCOUNTANT})"
post_json /dp/config operator "{\"clipping_norm\":${CLIP},\"noise_multiplier\":${NOISE},\"sample_rate\":${SAMPLE_RATE},\"delta\":${DELTA},\"accountant\":\"${ACCOUNTANT}\"}" | jq .

log "Step 4 — Select aggregator: ${STRATEGY}"
post_json /strategy operator "{\"strategy\":\"${STRATEGY}\"}" | jq .

log "Step 5 — Start training: session_id=${SESSION_ID}, rounds=${ROUNDS}"
post_json /training/start operator "{\"session_id\":\"${SESSION_ID}\",\"rounds\":${ROUNDS}}" | jq .

log "Step 6 — Monitor in Grafana"
log "Open Grafana at ${GRAFANA_URL} (see docs: technical/observability_and_dashboards.md)"
log "Tip: Filter dashboards by session_id='${SESSION_ID}' to isolate this run."

log "Step 7 — Poll training status..."
for i in $(seq 1 $((ROUNDS*20))); do
  status_json=$(get_json "/training/status?session_id=${SESSION_ID}" viewer)
  status=$(echo "$status_json" | jq -r '.status')
  cur=$(echo "$status_json" | jq -r '.current_round // 0')
  tot=$(echo "$status_json" | jq -r --argjson tot "$ROUNDS" '.total_rounds // $tot')
  eta=$(echo "$status_json" | jq -r '.eta_seconds // 0')
  eps=$(echo "$status_json" | jq -r '.epsilon_estimate // 0')
  log "status=${status} round=${cur}/${tot} eta=${eta}s epsilon≈${eps}"
  [[ "$status" == "completed" ]] && break
  sleep 1
done

log "Step 8 — Generate compliance report"
get_json /compliance/report viewer | jq -r .markdown > "${ARTIFACT_DIR}/report_${SESSION_ID}.md"
log "Report written: ${ARTIFACT_DIR}/report_${SESSION_ID}.md"

log "Done (Healthcare HIPAA playbook)."
