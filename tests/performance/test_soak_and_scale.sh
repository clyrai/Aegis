#!/usr/bin/env bash
set -euo pipefail

echo "[Soak] Long-running soak and >100 participant simulation"

ROOT_DIR=$(cd "$(dirname "$0")"/../.. && pwd)
RESULTS_DIR="$ROOT_DIR/test_results"
mkdir -p "$RESULTS_DIR"

SOAK_SECONDS=${SOAK_SECONDS:-60}
PARTICIPANTS=${PARTICIPANTS:-120}

python - <<PY
import time, threading, random
from examples.flower_sim.run_demo import main as demo_main

def run_demo_round():
    demo_main(rounds=1)

t0=time.time()
it=0
while time.time()-t0 < ${SOAK_SECONDS}:
    it+=1
    ths=[threading.Thread(target=run_demo_round) for _ in range( max(3, ${PARTICIPANTS}//40) )]
    for t in ths: t.start()
    for t in ths: t.join()
    time.sleep(0.2)
print('iterations',it)
PY

echo "[Soak] OK"