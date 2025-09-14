from __future__ import annotations

import subprocess
import sys
import time
import threading

import httpx

from aegis.api import app


def test_cli_demo_spawns_api_and_runs():
    # spawn uvicorn in thread
    import uvicorn

    class UThread(threading.Thread):
        def __init__(self):
            super().__init__(daemon=True)
            self.server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8010, log_level="warning"))
        def run(self):
            self.server.run()

    t = UThread()
    t.start()

    # wait for server
    for _ in range(50):
        try:
            httpx.get("http://127.0.0.1:8010/openapi.json")
            break
        except Exception:
            time.sleep(0.05)

    # run demo without spawning API (talk to 8010)
    proc = subprocess.run([sys.executable, "-m", "aegis.cli", "demo", "--no-spawn-api", "--port", "8010", "--url", "http://127.0.0.1:8010"], capture_output=True, text=True, timeout=20)
    assert proc.returncode == 0
    assert "Aegis Compliance Report" in proc.stdout
