#!/usr/bin/env bash
set -euo pipefail

# Healthcare-focused end-to-end demo
# - Starts Aegis API on a free port with mTLS-sim and file-backed audit
# - Registers 3 hospital participants
# - Applies conservative DP config
# - Selects Trimmed Mean strategy
# - Starts a short training session
# - Generates a Markdown report
# - Verifies audit integrity (JSONL)

if ! command -v python >/dev/null 2>&1; then
  echo "Python not found. Please install Python 3.10+" >&2
  exit 2
fi

if ! python -c 'import importlib; importlib.import_module("uvicorn")' >/dev/null 2>&1; then
  echo "uvicorn not installed in current environment. Try: pip install uvicorn fastapi" >&2
  exit 2
fi

FREE_PORT=$(python - <<'PY'
import socket
s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()
PY
)

WORKDIR=$(mktemp -d 2>/dev/null || mktemp -d -t aegis_demo)
AUDIT_FILE="$WORKDIR/audit.jsonl"
REPORT_FILE="$WORKDIR/report.md"
export REPORT_FILE

echo "Using port: $FREE_PORT"
echo "Working dir: $WORKDIR"

# Start API in background with simulated mTLS and file-backed audit
AEGIS_REQUIRE_MTLS_SIM=1 AEGIS_AUDIT_LOG_FILE="$AUDIT_FILE" \
  python -m uvicorn aegis.api:app --host 127.0.0.1 --port "$FREE_PORT" --log-level warning &
PID=$!
trap 'echo "Stopping API (PID=$PID)"; kill $PID 2>/dev/null || true' EXIT

# Wait for health
echo -n "Waiting for API..."
for i in {1..30}; do
  if curl -fsS "http://127.0.0.1:$FREE_PORT/healthz" >/dev/null; then
    echo " up"
    break
  fi
  sleep 0.5
  echo -n "."
done

base() { echo "http://127.0.0.1:$FREE_PORT"; }

echo "Registering participants..."
curl -fsS -X POST -H 'X-Role: admin' -H 'Content-Type: application/json' \
  -d '{"client_id":"hospital_a","key_hex":"aa"}' "$(base)/participants" >/dev/null
curl -fsS -X POST -H 'X-Role: admin' -H 'Content-Type: application/json' \
  -d '{"client_id":"hospital_b","key_hex":"bb"}' "$(base)/participants" >/dev/null
curl -fsS -X POST -H 'X-Role: admin' -H 'Content-Type: application/json' \
  -d '{"client_id":"hospital_c","key_hex":"cc"}' "$(base)/participants" >/dev/null

echo "Applying DP config..."
curl -fsS -X POST -H 'X-Role: operator' -H 'Content-Type: application/json' \
  -d '{"clipping_norm":1.0,"noise_multiplier":1.2,"sample_rate":0.01,"delta":1e-5,"accountant":"rdp"}' \
  "$(base)/dp/config" >/dev/null

echo "Assessing epsilon for 10000 steps..."
curl -fsS -H 'X-Role: operator' "$(base)/dp/assess?steps=10000" | tee "$WORKDIR/epsilon.json" >/dev/null

echo "Selecting strategy: trimmed_mean"
curl -fsS -X POST -H 'X-Role: operator' -H 'Content-Type: application/json' \
  -d '{"strategy":"trimmed_mean"}' "$(base)/strategy" >/dev/null

echo "Starting training session..."
curl -fsS -X POST -H 'X-Role: operator' -H 'Content-Type: application/json' \
  -d '{"session_id":"s1","rounds":3}' "$(base)/training/start" >/dev/null

echo "Fetching training status..."
curl -fsS -H 'X-Role: viewer' "$(base)/training/status?session_id=s1" | tee "$WORKDIR/status.json" >/dev/null

echo "Generating compliance report (markdown)..."
curl -fsS -H 'Accept: application/json' -H 'X-Role: viewer' -H 'X-Client-Cert: 1' \
  "$(base)/compliance/report" -o "$WORKDIR/report.json"
python - <<'PY'
import sys, json, os
p=os.environ.get('REPORT_FILE') or 'report.md'
with open(os.path.join(os.path.dirname(p),'report.json')) as f:
    data=json.load(f)
md=data.get('markdown','')
with open(p,'w') as f:
    f.write(md)
print(p)
PY

echo "Report saved to: $REPORT_FILE"

echo "Verifying audit integrity (JSONL)..."
python -m aegis.tools.audit_verify jsonl "$AUDIT_FILE"

echo
echo "Done. Explore artifacts in: $WORKDIR"
echo "- Report: $REPORT_FILE"
echo "- Audit:  $AUDIT_FILE"
echo "- Epsilon assessment: $WORKDIR/epsilon.json"
echo "- Status: $WORKDIR/status.json"
