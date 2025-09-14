#!/usr/bin/env bash
set -euo pipefail

echo "[Performance] Stress scenarios"

ROOT_DIR=$(cd "$(dirname "$0")"/../.. && pwd)
RESULTS_DIR="$ROOT_DIR/test_results"
mkdir -p "$RESULTS_DIR"

echo "[Performance] CPU burst (compute-bound loop)"
python - <<'PY'
import time, math
t0=time.perf_counter()
acc=0.0
for i in range(5_000_000):
	acc+=math.sin(i*0.001)
print('acc',acc,'elapsed',time.perf_counter()-t0)
PY

echo "[Performance] Memory pressure (allocate ~100MB then free)"
python - <<'PY'
import time
data=bytearray(100*1024*1024)
for i in range(0,len(data),4096): data[i]=i%256
del data
print('allocated and freed')
PY

echo "[Performance] OK"
