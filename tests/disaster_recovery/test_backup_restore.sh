#!/usr/bin/env bash
set -euo pipefail

echo "[DR] Backup/restore"

ROOT_DIR=$(cd "$(dirname "$0")"/../.. && pwd)
cd "$ROOT_DIR"
TMP_FILE=$(mktemp /tmp/aegis_audit.XXXXXX.jsonl)
export AEGIS_AUDIT_LOG_FILE="$TMP_FILE"
export AEGIS_REQUIRE_MTLS_SIM=0

PORT=$(python - <<'PY'
import socket
s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()
PY
)

python - <<PY &
import uvicorn
from aegis.api import app
uvicorn.run(app, host="127.0.0.1", port=$PORT, log_level="warning")
PY
PID=$!
sleep 0.5

python - <<PY
import httpx
base=f"http://127.0.0.1:$PORT"
httpx.post(f"{base}/participants", headers={"X-Role":"admin"}, json={"client_id":"c1","key_hex":"aa"}).raise_for_status()
print(httpx.get(f"{base}/audit/checksum", headers={"X-Role":"viewer"}).json())
PY

kill -9 $PID || true
sleep 0.5

echo "[DR] Simulate restore by restarting with same audit file"
python - <<PY &
import uvicorn
from aegis.api import app
uvicorn.run(app, host="127.0.0.1", port=$PORT, log_level="warning")
PY
PID2=$!
sleep 0.5

python - <<PY
import httpx,sys
base=f"http://127.0.0.1:$PORT"
r=httpx.get(f"{base}/audit/checksum", headers={"X-Role":"viewer"})
print(r.json())
sys.exit(0 if r.status_code==200 else 1)
PY

kill -9 $PID2 || true
rm -f "$TMP_FILE"
echo "[DR] OK"
