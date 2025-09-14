#!/usr/bin/env bash
set -euo pipefail

# Compare baseline vs stricter DP configs and generate two reports

if ! command -v python >/dev/null 2>&1; then
  echo "Python not found. Please install Python 3.10+" >&2
  exit 2
fi
if ! python -c 'import importlib; importlib.import_module("uvicorn")' >/dev/null 2>&1; then
  echo "uvicorn not installed. Try: pip install uvicorn fastapi" >&2
  exit 2
fi

FREE_PORT=$(python - <<'PY'
import socket
s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()
PY
)
WORKDIR=$(mktemp -d 2>/dev/null || mktemp -d -t aegis_tune_dp)
export WORKDIR
echo "Using port: $FREE_PORT"
echo "Working dir: $WORKDIR"

AEGIS_REQUIRE_MTLS_SIM=1 python -m uvicorn aegis.api:app --host 127.0.0.1 --port "$FREE_PORT" --log-level warning &
PID=$!
trap 'kill $PID 2>/dev/null || true' EXIT

echo -n "Waiting for API..."
up=0
for i in {1..60}; do
  if curl -fsS "http://127.0.0.1:$FREE_PORT/healthz" >/dev/null 2>&1; then up=1; echo " up"; break; fi
  sleep 0.25
  echo -n "."
done
if [ "$up" -ne 1 ]; then
  echo "\nAPI did not become ready in time" >&2
  exit 1
fi

base() { echo "http://127.0.0.1:$FREE_PORT"; }

# Minimal participant so session metadata exists if needed
curl -fsS -X POST -H 'X-Role: admin' -H 'Content-Type: application/json' \
  -d '{"client_id":"hospital_a","key_hex":"aa"}' "$(base)/participants" >/dev/null || true

steps=10000

echo "Baseline DP (nm=1.2)"
curl -fsS -X POST -H 'X-Role: operator' -H 'Content-Type: application/json' \
  -d '{"clipping_norm":1.0,"noise_multiplier":1.2,"sample_rate":0.01,"delta":1e-5,"accountant":"rdp"}' \
  "$(base)/dp/config" >/dev/null
curl -fsS -H 'X-Role: operator' "$(base)/dp/assess?steps=$steps" -o "$WORKDIR/epsilon_baseline.json"
curl -fsS -H 'Accept: application/json' -H 'X-Role: viewer' -H 'X-Client-Cert: 1' \
  "$(base)/compliance/report" -o "$WORKDIR/report_baseline.json"
python - <<'PY'
import json, os
wj=os.path.join(os.environ['WORKDIR'],'report_baseline.json')
wm=os.path.join(os.environ['WORKDIR'],'report_baseline.md')
with open(wj) as f:
    d=json.load(f)
open(wm,'w').write(d.get('markdown',''))
print('baseline_epsilon_json:', os.path.join(os.environ['WORKDIR'],'epsilon_baseline.json'))
print('baseline_report_md:', wm)
PY

echo "Stricter DP (nm=2.0)"
curl -fsS -X POST -H 'X-Role: operator' -H 'Content-Type: application/json' \
  -d '{"clipping_norm":1.0,"noise_multiplier":2.0,"sample_rate":0.01,"delta":1e-5,"accountant":"rdp"}' \
  "$(base)/dp/config" >/dev/null
curl -fsS -H 'X-Role: operator' "$(base)/dp/assess?steps=$steps" -o "$WORKDIR/epsilon_stricter.json"
curl -fsS -H 'Accept: application/json' -H 'X-Role: viewer' -H 'X-Client-Cert: 1' \
  "$(base)/compliance/report" -o "$WORKDIR/report_stricter.json"
python - <<'PY'
import json, os
wj=os.path.join(os.environ['WORKDIR'],'report_stricter.json')
wm=os.path.join(os.environ['WORKDIR'],'report_stricter.md')
with open(wj) as f:
    d=json.load(f)
open(wm,'w').write(d.get('markdown',''))
print('stricter_epsilon_json:', os.path.join(os.environ['WORKDIR'],'epsilon_stricter.json'))
print('stricter_report_md:', wm)
PY

echo
echo "Artifacts: $WORKDIR"
echo "- epsilon_baseline.json"
echo "- epsilon_stricter.json"
echo "- report_baseline.md"
echo "- report_stricter.md"