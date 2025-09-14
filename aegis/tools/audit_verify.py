"""
Audit verification tool: validates integrity of Aegis audit logs.

Supports:
- JSONL hash-chained logs (file-backed)
- SQLite logs with HMAC signatures

Exit codes:
 0 - OK
 1 - Integrity failure
 2 - Usage or unexpected error
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional


@dataclass
class VerifyResult:
    ok: bool
    checked: int
    failed_index: Optional[int] = None
    message: str = ""


def _iter_jsonl(path: Path) -> Iterator[dict]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def verify_jsonl(path: str) -> VerifyResult:
    p = Path(path)
    if not p.exists():
        return VerifyResult(False, 0, None, f"File not found: {path}")

    prev_curr: Optional[str] = None
    checked = 0
    for idx, rec in enumerate(_iter_jsonl(p)):
        # Support two schemas:
        # 1) Generic: {payload, prev_hash, curr_hash}
        # 2) Aegis:  {timestamp, actor, action, params_hash, outcome, prev_hash}
        if "curr_hash" in rec or "payload" in rec:
            payload = rec.get("payload")
            chain_prev = rec.get("prev_hash")
            chain_curr = rec.get("curr_hash")
            if payload is None or chain_curr is None:
                return VerifyResult(False, checked, idx, "Missing payload or curr_hash")
            m = hashlib.sha256()
            if prev_curr:
                m.update(prev_curr.encode())
            if chain_prev and prev_curr and chain_prev != prev_curr:
                return VerifyResult(False, checked, idx, "prev_hash mismatch")
            m.update(json.dumps(payload, sort_keys=True).encode())
            computed = m.hexdigest()
            if computed != chain_curr:
                return VerifyResult(False, checked, idx, "curr_hash mismatch")
            prev_curr = chain_curr
        else:
            # Aegis schema: verify linkage prev_hash == previous params_hash
            params_hash = rec.get("params_hash")
            chain_prev = rec.get("prev_hash")
            if not params_hash:
                return VerifyResult(False, checked, idx, "Missing params_hash")
            # For first record, any prev_hash is accepted; for others, it must match previous params_hash
            if checked > 0 and chain_prev != prev_curr:
                return VerifyResult(False, checked, idx, "prev_hash linkage mismatch")
            prev_curr = params_hash
        checked += 1

    return VerifyResult(True, checked, None, "OK")


def verify_sqlite(db_path: str, hmac_key_env: str = "AEGIS_AUDIT_HMAC_KEY") -> VerifyResult:
    if not os.path.exists(db_path):
        return VerifyResult(False, 0, None, f"DB not found: {db_path}")
    key = os.getenv(hmac_key_env)
    if not key:
        return VerifyResult(False, 0, None, f"HMAC key env var not set: {hmac_key_env}")

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        # Aegis schema
        cur.execute("SELECT id, params_hash, prev_hash, signature FROM audit_events ORDER BY id ASC")
        rows = cur.fetchall()
        checked = 0
        prev_params: Optional[str] = None
        for row in rows:
            idx, params_hash, prev_hash, signature = row
            # Linkage check
            if checked > 0 and prev_hash != prev_params:
                return VerifyResult(False, checked, idx, "prev_hash linkage mismatch")
            # HMAC check if signature present
            if signature is not None:
                mac = hmac.new(key.encode(), (params_hash + (prev_hash or "")).encode(), hashlib.sha256).hexdigest()
                if mac != signature:
                    return VerifyResult(False, checked, idx, "HMAC signature mismatch")
            prev_params = params_hash
            checked += 1
        return VerifyResult(True, checked, None, "OK")
    finally:
        conn.close()


def main(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Verify Aegis audit logs")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_jsonl = sub.add_parser("jsonl", help="Verify JSONL hash-chained logs")
    p_jsonl.add_argument("path", help="Path to JSONL log file")

    p_sqlite = sub.add_parser("sqlite", help="Verify SQLite HMAC logs")
    p_sqlite.add_argument("db", help="Path to SQLite DB file")
    p_sqlite.add_argument("--hmac-key-env", default="AEGIS_AUDIT_HMAC_KEY", help="Env var name for HMAC key")

    args = parser.parse_args(argv)

    try:
        if args.mode == "jsonl":
            res = verify_jsonl(args.path)
        else:
            res = verify_sqlite(args.db, args.hmac_key_env)
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if res.ok:
        print(f"OK - checked={res.checked}")
        return 0
    else:
        print(f"FAIL - checked={res.checked} idx={res.failed_index} msg={res.message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
