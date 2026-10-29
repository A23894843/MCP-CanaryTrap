# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""Small SQLite persistence layer for demo sessions, events and verdicts."""
# Explanation: Imports modules that this file uses.
import json
# Explanation: Imports modules that this file uses.
import os
# Explanation: Imports modules that this file uses.
import sqlite3
# Explanation: Imports names from pathlib.
from pathlib import Path
# Explanation: Imports names from typing.
from typing import Any
# Explanation: Imports names from events.
from .events import InteractionEvent
# Explanation: Imports names from verdict.
from .verdict import Verdict

# Explanation: Sets a module-level constant or configuration value.
DEFAULT_DB = Path(os.getenv("CANARYTRAP_DB", "canarytrap.sqlite3"))

# Explanation: Class Store: groups related data and operations.
class Store:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Database helper; each operation opens its own short-lived connection."""
    # Explanation: Function __init__: implements the operation described by its name and body.
    def __init__(self, path: str | Path = DEFAULT_DB):
        # Explanation: Assigns or updates a value used later by this function or module.
        self.path = Path(path)
        # Explanation: Assigns or updates a value used later by this function or module.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        self.initialize()

    # Explanation: Function connect: Open a row-addressable SQLite connection.
    def connect(self) -> sqlite3.Connection:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        """Open a row-addressable SQLite connection."""
        # Explanation: Assigns or updates a value used later by this function or module.
        connection = sqlite3.connect(self.path)
        # Explanation: Assigns or updates a value used later by this function or module.
        connection.row_factory = sqlite3.Row
        # Explanation: Return this result to the caller; this ends the current function path.
        return connection

    # Explanation: Function initialize: Create schema if it does not already exist.
    def initialize(self) -> None:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        """Create schema if it does not already exist."""
        # Explanation: Acquire/manage the context resource and release it reliably on exit.
        with self.connect() as db:
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            db.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY, scenario TEXT NOT NULL,
                    created_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'RUNNING',
                    summary TEXT NOT NULL DEFAULT '', tenant TEXT NOT NULL DEFAULT 'default'
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
                CREATE TABLE IF NOT EXISTS gateway_connections (
                    connection_id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    token_env TEXT NOT NULL DEFAULT '',
                    decoy_tools_json TEXT NOT NULL DEFAULT '[]',
                    decoy_resources_json TEXT NOT NULL DEFAULT '[]',
                    decoy_prompts_json TEXT NOT NULL DEFAULT '[]',
                    updated_at TEXT NOT NULL
                );
            """)
            # Backward-compatible migration for databases created before tenant scoping.
            # Explanation: Assigns or updates a value used later by this function or module.
            session_columns = {row["name"] for row in db.execute("PRAGMA table_info(sessions)").fetchall()}
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if "tenant" not in session_columns:
                # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
                db.execute("ALTER TABLE sessions ADD COLUMN tenant TEXT NOT NULL DEFAULT 'default'")

    # Explanation: Function create_session: Register a session before storing its events, scoped to a tenant.
    def create_session(self, session_id: str, scenario: str, created_at: str, tenant: str = "default") -> None:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        """Register a session before storing its events, scoped to a tenant."""
        # Explanation: Acquire/manage the context resource and release it reliably on exit.
        with self.connect() as db:
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            db.execute("INSERT INTO sessions(session_id, scenario, created_at, tenant) VALUES(?,?,?,?)",
                       (session_id, scenario, created_at, tenant))

    # Explanation: Function add_event: Persist one interaction event.
    def add_event(self, event: InteractionEvent) -> None:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        """Persist one interaction event."""
        # Explanation: Acquire/manage the context resource and release it reliably on exit.
        with self.connect() as db:
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            db.execute("""INSERT INTO events
                (event_id,session_id,timestamp,operation,target,target_kind,is_decoy,details)
                VALUES(?,?,?,?,?,?,?,?)""", (event.event_id, event.session_id, event.timestamp,
                event.operation, event.target, event.target_kind, int(event.is_decoy), event.details))

    # Explanation: Function save_verdict: Persist final session verdict and evidence identifiers.
    def save_verdict(self, verdict: Verdict) -> None:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        """Persist final session verdict and evidence identifiers."""
        # Explanation: Acquire/manage the context resource and release it reliably on exit.
        with self.connect() as db:
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            db.execute("INSERT OR REPLACE INTO verdicts VALUES(?,?,?,?,?)",
                       (verdict.session_id, verdict.status, verdict.reason,
                        json.dumps(list(verdict.evidence_event_ids)), verdict.evaluated_at))
            # Explanation: Assigns or updates a value used later by this function or module.
            db.execute("UPDATE sessions SET status=?, summary=? WHERE session_id=?",
                       (verdict.status, verdict.reason, verdict.session_id))

    # Explanation: Function list_sessions: Return sessions newest first, optionally restricted to one tenant.
    def list_sessions(self, tenant: str | None = None) -> list[dict[str, Any]]:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        """Return sessions newest first, optionally restricted to one tenant."""
        # Explanation: Acquire/manage the context resource and release it reliably on exit.
        with self.connect() as db:
            # Explanation: Assigns or updates a value used later by this function or module.
            query = """SELECT s.*, v.reason, v.evidence_json, v.evaluated_at
                FROM sessions s LEFT JOIN verdicts v USING(session_id)"""
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if tenant is not None:
                # Explanation: Assigns or updates a value used later by this function or module.
                rows = db.execute(query + " WHERE s.tenant=? ORDER BY s.created_at DESC", (tenant,)).fetchall()
            else:
                # Explanation: Assigns or updates a value used later by this function or module.
                rows = db.execute(query + " ORDER BY s.created_at DESC").fetchall()
        # Explanation: Assigns or updates a value used later by this function or module.
        result = []
        # Explanation: Loop over each item in the iterable and run the indented body.
        for row in rows:
            # Explanation: Assigns or updates a value used later by this function or module.
            item = dict(row)
            # Explanation: Assigns or updates a value used later by this function or module.
            item["evidence_event_ids"] = json.loads(item.pop("evidence_json") or "[]")
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            result.append(item)
        # Explanation: Return this result to the caller; this ends the current function path.
        return result

    # Explanation: Function list_events: Return recent events, optionally filtered by session and tenant.
    def list_events(self, session_id: str | None = None, tenant: str | None = None) -> list[dict[str, Any]]:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        """Return recent events, optionally filtered by session and tenant."""
        # Explanation: Acquire/manage the context resource and release it reliably on exit.
        with self.connect() as db:
            # Explanation: Assigns or updates a value used later by this function or module.
            query = "SELECT e.* FROM events e JOIN sessions s USING(session_id)"
            # Explanation: Assigns or updates a value used later by this function or module.
            clauses, params = [], []
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if session_id:
                # Explanation: Assigns or updates a value used later by this function or module.
                clauses.append("e.session_id=?"); params.append(session_id)
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if tenant is not None:
                # Explanation: Assigns or updates a value used later by this function or module.
                clauses.append("s.tenant=?"); params.append(tenant)
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if clauses:
                # Explanation: Assigns or updates a value used later by this function or module.
                query += " WHERE " + " AND ".join(clauses)
            # Explanation: Assigns or updates a value used later by this function or module.
            query += " ORDER BY e.timestamp" + ("" if session_id else " DESC LIMIT 500")
            # Explanation: Assigns or updates a value used later by this function or module.
            rows = db.execute(query, tuple(params)).fetchall()
        # Explanation: Return this result to the caller; this ends the current function path.
        return [dict(row) | {"is_decoy": bool(row["is_decoy"])} for row in rows]

    # Explanation: Function get_session: Return one session summary, optionally restricted to its tenant.
    def get_session(self, session_id: str, tenant: str | None = None) -> dict[str, Any] | None:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        """Return one session summary, optionally restricted to its tenant."""
        # Explanation: Return this result to the caller; this ends the current function path.
        return next((s for s in self.list_sessions(tenant=tenant) if s["session_id"] == session_id), None)

    # Explanation: Function save_gateway_connection: Persist non-secret HTTP upstream configuration; secret values are never stored.
    def save_gateway_connection(self, connection: dict[str, Any]) -> None:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        """Persist non-secret HTTP upstream configuration; secret values are never stored."""
        # Explanation: Imports names from datetime.
        from datetime import datetime, timezone
        # Explanation: Acquire/manage the context resource and release it reliably on exit.
        with self.connect() as db:
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            db.execute("""INSERT INTO gateway_connections
                (connection_id,url,token_env,decoy_tools_json,decoy_resources_json,decoy_prompts_json,updated_at)
                VALUES(?,?,?,?,?,?,?) ON CONFLICT(connection_id) DO UPDATE SET
                url=excluded.url, token_env=excluded.token_env,
                decoy_tools_json=excluded.decoy_tools_json,
                decoy_resources_json=excluded.decoy_resources_json,
                decoy_prompts_json=excluded.decoy_prompts_json, updated_at=excluded.updated_at""",
                (connection["id"], connection["url"], connection.get("token_env", ""),
                 json.dumps(connection.get("decoy_tools", [])),
                 json.dumps(connection.get("decoy_resources", [])),
                 json.dumps(connection.get("decoy_prompts", [])),
                 datetime.now(timezone.utc).isoformat()))

    # Explanation: Function list_gateway_connections: Load saved non-secret HTTP upstream definitions keyed by connection ID.
    def list_gateway_connections(self) -> dict[str, dict[str, Any]]:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        """Load saved non-secret HTTP upstream definitions keyed by connection ID."""
        # Explanation: Acquire/manage the context resource and release it reliably on exit.
        with self.connect() as db:
            # Explanation: Assigns or updates a value used later by this function or module.
            rows = db.execute("SELECT * FROM gateway_connections ORDER BY connection_id").fetchall()
        # Explanation: Assigns or updates a value used later by this function or module.
        result: dict[str, dict[str, Any]] = {}
        # Explanation: Loop over each item in the iterable and run the indented body.
        for row in rows:
            # Explanation: Assigns or updates a value used later by this function or module.
            result[row["connection_id"]] = {
                "url": row["url"], "token_env": row["token_env"],
                "decoy_tools": json.loads(row["decoy_tools_json"]),
                "decoy_resources": json.loads(row["decoy_resources_json"]),
                "decoy_prompts": json.loads(row["decoy_prompts_json"]),
            }
        # Explanation: Return this result to the caller; this ends the current function path.
        return result

    # Explanation: Function delete_gateway_connection: Delete a dashboard-saved connection; environment-defined entries are unaffected.
    def delete_gateway_connection(self, connection_id: str) -> bool:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        """Delete a dashboard-saved connection; environment-defined entries are unaffected."""
        # Explanation: Acquire/manage the context resource and release it reliably on exit.
        with self.connect() as db:
            # Explanation: Assigns or updates a value used later by this function or module.
            cursor = db.execute("DELETE FROM gateway_connections WHERE connection_id=?", (connection_id,))
            # Explanation: Return this result to the caller; this ends the current function path.
            return cursor.rowcount > 0
