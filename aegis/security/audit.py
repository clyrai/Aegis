from __future__ import annotations

import hashlib
import os
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import hmac
import sqlite3


@dataclass
class AuditEvent:
    timestamp: str
    actor: str
    action: str
    params_hash: str
    outcome: str
    prev_hash: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"))


class AuditLogger:
    def __init__(self) -> None:
        self._prev: Optional[str] = None
        self._log = logging.getLogger("aegis.audit")
        # Store events in-memory for compliance/audit testing
        self._events = []
        self._outfile = os.environ.get("AEGIS_AUDIT_LOG_FILE")
        # Optional durable backend (SQLite) with simple daily rotation
        self._sqlite_path = os.environ.get("AEGIS_AUDIT_SQLITE_PATH")
        self._hmac_key = os.environ.get("AEGIS_AUDIT_HMAC_KEY")
        self._sqlite_conn: Optional[sqlite3.Connection] = None
        if self._sqlite_path:
            self._sqlite_conn = self._open_sqlite()

    def _rotated_sqlite_path(self) -> str:
        assert self._sqlite_path is not None
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        if "{date}" in self._sqlite_path:
            return self._sqlite_path.format(date=today)
        base = self._sqlite_path
        # append date before extension if present
        if "." in os.path.basename(base):
            root, ext = os.path.splitext(base)
            return f"{root}.{today}{ext}"
        return f"{base}.{today}.sqlite"

    def _open_sqlite(self) -> sqlite3.Connection:
        path = self._rotated_sqlite_path()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        conn = sqlite3.connect(path, isolation_level=None)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                params_hash TEXT NOT NULL,
                outcome TEXT NOT NULL,
                prev_hash TEXT,
                signature TEXT
            )
            """
        )
        return conn

    def _hmac_sign(self, params_hash: str, prev_hash: Optional[str]) -> Optional[str]:
        if not self._hmac_key:
            return None
        key = self._hmac_key.encode()
        msg = (params_hash + (prev_hash or "")).encode()
        return hmac.new(key, msg, hashlib.sha256).hexdigest()

    def emit(self, actor: str, action: str, params: Dict[str, Any], outcome: str) -> AuditEvent:
        ts = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(params, separators=(",", ":")).encode()
        ph = self._prev.encode() if self._prev else b""
        h = hashlib.sha256(ph + payload).hexdigest()
        evt = AuditEvent(timestamp=ts, actor=actor, action=action, params_hash=h, outcome=outcome, prev_hash=self._prev)
        try:
            self._log.info("audit", extra={"event": asdict(evt)})
            # Best-effort file append if configured
            if self._outfile:
                with open(self._outfile, "a", encoding="utf-8") as fh:
                    fh.write(evt.to_json() + "\n")
            # Best-effort SQLite insert if configured
            if self._sqlite_conn is not None:
                sig = self._hmac_sign(evt.params_hash, evt.prev_hash)
                self._sqlite_conn.execute(
                    "INSERT INTO audit_events (timestamp, actor, action, params_hash, outcome, prev_hash, signature) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (evt.timestamp, evt.actor, evt.action, evt.params_hash, evt.outcome, evt.prev_hash, sig),
                )
        except Exception:
            # Logging handler misconfig shouldn't break audit chain; continue silently.
            pass
        self._prev = h
        self._events.append(evt)
        return evt

    def events(self):
        return list(self._events)

    def verify_chain(self) -> bool:
        for i in range(1, len(self._events)):
            if self._events[i].prev_hash != self._events[i - 1].params_hash:
                return False
        return True

    def checksum(self) -> str:
        """Compute a chain checksum as sha256 of concatenated params_hash values."""
        if not self._events:
            return hashlib.sha256(b"").hexdigest()
        data = b"".join(e.params_hash.encode() for e in self._events)
        return hashlib.sha256(data).hexdigest()
