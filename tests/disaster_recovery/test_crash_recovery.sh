#!/usr/bin/env bash
set -euo pipefail

echo "[DR] Mid-training crash recovery"

ROOT_DIR=$(cd "$(dirname "$0")"/../.. && pwd)
cd "$ROOT_DIR"

PORT=$(python - <<'PY'
import socket
s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()
PY
)

export AEGIS_REQUIRE_MTLS_SIM=0

python - <<PY &
import uvicorn
from aegis.api import app
uvicorn.run(app, host="127.0.0.1", port=$PORT, log_level="warning")
PY
PID=$!

echo "[DR] Start training session"
python - <<PY
import httpx
base=f"http://127.0.0.1:$PORT"
httpx.post(f"{base}/participants", headers={"X-Role":"admin"}, json={"client_id":"c1","key_hex":"aa"}).raise_for_status()
httpx.post(f"{base}/training/start", headers={"X-Role":"operator"}, json={"session_id":"s1","rounds":5}).raise_for_status()
print('started')
PY

echo "[DR] Simulate crash"
kill -9 $PID || true
sleep 0.5

echo "[DR] Restart"
python - <<PY &
import uvicorn
from aegis.api import app
uvicorn.run(app, host="127.0.0.1", port=$PORT, log_level="warning")
PY
PID2=$!
sleep 0.5

echo "[DR] Verify API responds after restart"
python - <<PY
import httpx,sys
base=f"http://127.0.0.1:$PORT"
r=httpx.get(f"{base}/healthz")
sys.exit(0 if r.status_code==200 else 1)
PY

kill -9 $PID2 || true
echo "[DR] OK"
