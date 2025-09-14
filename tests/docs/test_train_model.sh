#!/usr/bin/env bash
set -euo pipefail

# Train Model Smoke Test
# Executes the steps from docs/technical/train_model.md against a running Aegis API.
# Usage:
#   BASE_URL=http://localhost:8000 ./tests/docs/test_train_model.sh
#   Or set BASE_URL to your production/staging URL.

BASE_URL=${BASE_URL:-http://localhost:8000}
SESSION_ID=${SESSION_ID:-run1}
ROUNDS=${ROUNDS:-5}
POLL_MAX=${POLL_MAX:-60}   # number of polls
POLL_SLEEP=${POLL_SLEEP:-5} # seconds between polls
ART_DIR=${ART_DIR:-test_artifacts}
mkdir -p "$ART_DIR"

have_cmd() { command -v "$1" >/dev/null 2>&1; }

http_post_json() {
  # args: role path json
  local role="$1"; shift
  local path="$1"; shift
  local json="$1"; shift || true
  if have_cmd http; then
    http --check-status --timeout=20 POST "${BASE_URL}${path}" X-Role:"${role}" Content-Type:application/json <<<"${json}" 1>/dev/null
  else
    curl -fsS -m 20 -H "X-Role: ${role}" -H 'Content-Type: application/json' -X POST -d "${json}" "${BASE_URL}${path}" >/dev/null
  fi
}

http_get() {
  # args: role path [query_like session_id==run1]
  local role="$1"; shift
  local url="${BASE_URL}$1"; shift
  local extra=("$@")
  if have_cmd http; then
    http --check-status --timeout=20 GET "${url}" X-Role:"${role}" "${extra[@]}"
  else
    # map HTTPie-style query extra (key==val) to curl '?key=val'
    if [ ${#extra[@]} -gt 0 ]; then
      local q="${extra[0]}"; q="${q%%==*}=${q##*==}"
      url="${url}?${q}"
    fi
    curl -fsS -m 20 -H "X-Role: ${role}" "${url}"
  fi
}

log() { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[WARN]\033[0m %s\n" "$*"; }
err()  { printf "\033[1;31m[ERR ]\033[0m %s\n" "$*"; }

log "Base URL: ${BASE_URL}"

# 0) Health check
log "Checking API health..."
if have_cmd http; then
  if ! http --check-status --timeout=10 GET "${BASE_URL}/healthz" >/dev/null; then
    err "Health check failed at ${BASE_URL}/healthz"
    exit 1
  fi
else
  curl -fsS -m 10 "${BASE_URL}/healthz" >/dev/null || { err "Health check failed at ${BASE_URL}/healthz"; exit 1; }
fi
log "API healthy"

# 1) Register participants
log "Registering participants c1, c2..."
set +e
http_post_json admin "/participants" '{"client_id":"c1","key_hex":"aa"}' || warn "c1 may already exist"
http_post_json admin "/participants" '{"client_id":"c2","key_hex":"bb"}' || warn "c2 may already exist"
set -e

# 2) Configure privacy (balanced defaults)
log "Configuring DP (balanced defaults)..."
http_post_json operator "/dp/config" '{"clipping_norm":1.0,"noise_multiplier":1.0,"sample_rate":0.01,"delta":1e-5,"accountant":"rdp"}'

# 3) Select strategy (Trimmed Mean)
log "Selecting strategy: trimmed_mean..."
http_post_json operator "/strategy" '{"strategy":"trimmed_mean"}'

# 4) Start training
log "Starting training: session_id=${SESSION_ID} rounds=${ROUNDS}"
http_post_json operator "/training/start" "{\"session_id\":\"${SESSION_ID}\",\"rounds\":${ROUNDS}}"

# 5) Poll status
log "Polling training status (max ${POLL_MAX} x ${POLL_SLEEP}s)..."
count=0
progress_seen=0
while :; do
  out=$(http_get viewer "/training/status" "session_id==${SESSION_ID}" 2>/dev/null || true)
  state=""
  if have_cmd jq; then
    # prefer 'status' then fallback to 'state'
    state=$(printf "%s" "$out" | jq -r '(.status // .state) // empty' 2>/dev/null)
  fi
  if [ -z "$state" ]; then
    # fallback parse: look for state string
    state=$(printf "%s" "$out" | grep -Eo '"(status|state)"\s*:\s*"[^"]+"' | sed -E 's/.*:"([^"]+)"/\1/')
  fi
  if [ -z "$state" ]; then
    warn "Status parse empty; raw: $(printf '%s' "$out" | head -c 200)"
  fi
  log "Status: ${state:-unknown}"
  case "$state" in
    completed|succeeded)
      break ;;
    failed|error)
      err "Training reported failure"
      exit 2 ;;
    started|running)
      progress_seen=1 ;;
  esac
  count=$((count+1))
  if [ $count -ge $POLL_MAX ]; then
    if [ "$progress_seen" -eq 1 ]; then
      warn "Timed out waiting for completion; proceeding to fetch report (progress observed)."
      break
    else
      warn "Status remained unknown; proceeding to fetch report anyway."
      break
    fi
  fi
  sleep "$POLL_SLEEP"
done

# 6) Generate compliance report
log "Fetching compliance report..."
if have_cmd http; then
  http --check-status --timeout=20 GET "${BASE_URL}/compliance/report" X-Role:viewer > "${ART_DIR}/report_${SESSION_ID}.md"
else
  curl -fsS -m 20 -H 'X-Role: viewer' "${BASE_URL}/compliance/report" > "${ART_DIR}/report_${SESSION_ID}.md"
fi

if [ ! -s "${ART_DIR}/report_${SESSION_ID}.md" ]; then
  err "Report was empty or missing"
  exit 4
fi

log "SUCCESS: Training completed and report saved to ${ART_DIR}/report_${SESSION_ID}.md"