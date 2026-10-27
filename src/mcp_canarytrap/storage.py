"""Small SQLite persistence layer for demo sessions, events and verdicts."""
import json
import os
import sqlite3
from pathlib import Path
from typing import Any
from .events import InteractionEvent
from .verdict import Verdict

DEFAULT_DB = Path(os.getenv("CANARYTRAP_DB", "canarytrap.sqlite3"))

class Store:
    """Database helper; each operation opens its own short-lived connection."""
    def __init__(self, path: str | Path = DEFAULT_DB):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        """Open a row-addressable SQLite connection."""
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        """Create schema if it does not already exist."""
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY, scenario TEXT NOT NULL,
                    created_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'RUNNING',
                    summary TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL, operation TEXT NOT NULL,
                    target TEXT NOT NULL, target_kind TEXT NOT NULL,
                    is_decoy INTEGER NOT NULL, details TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );
                CREATE TABLE IF NOT EXISTS verdicts (
                    session_id TEXT PRIMARY KEY, status TEXT NOT NULL,
                    reason TEXT NOT NULL, evidence_json TEXT NOT NULL,
                    evaluated_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );
            """)

    def create_session(self, session_id: str, scenario: str, created_at: str) -> None:
        """Register a session before storing its events."""
        with self.connect() as db:
            db.execute("INSERT INTO sessions(session_id, scenario, created_at) VALUES(?,?,?)",
                       (session_id, scenario, created_at))

    def add_event(self, event: InteractionEvent) -> None:
        """Persist one interaction event."""
        with self.connect() as db:
            db.execute("""INSERT INTO events
                (event_id,session_id,timestamp,operation,target,target_kind,is_decoy,details)
                VALUES(?,?,?,?,?,?,?,?)""", (event.event_id, event.session_id, event.timestamp,
                event.operation, event.target, event.target_kind, int(event.is_decoy), event.details))

    def save_verdict(self, verdict: Verdict) -> None:
        """Persist final session verdict and evidence identifiers."""
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO verdicts VALUES(?,?,?,?,?)",
                       (verdict.session_id, verdict.status, verdict.reason,
                        json.dumps(list(verdict.evidence_event_ids)), verdict.evaluated_at))
            db.execute("UPDATE sessions SET status=?, summary=? WHERE session_id=?",
                       (verdict.status, verdict.reason, verdict.session_id))

    def list_sessions(self) -> list[dict[str, Any]]:
        """Return sessions newest first with verdict fields where available."""
        with self.connect() as db:
            rows = db.execute("""SELECT s.*, v.reason, v.evidence_json, v.evaluated_at
                FROM sessions s LEFT JOIN verdicts v USING(session_id)
                ORDER BY s.created_at DESC""").fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["evidence_event_ids"] = json.loads(item.pop("evidence_json") or "[]")
            result.append(item)
        return result

    def list_events(self, session_id: str | None = None) -> list[dict[str, Any]]:
        """Return recorded events, optionally filtered to one session."""
        with self.connect() as db:
            if session_id:
                rows = db.execute("SELECT * FROM events WHERE session_id=? ORDER BY timestamp", (session_id,)).fetchall()
            else:
                rows = db.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT 500").fetchall()
        return [dict(row) | {"is_decoy": bool(row["is_decoy"])} for row in rows]

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Return one session summary, or None when unknown."""
        return next((s for s in self.list_sessions() if s["session_id"] == session_id), None)
