import sqlite3
import json
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "canarytrap.db"

def _connect():
    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def create_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evidence_chain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payload_json TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL UNIQUE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

def save_event(target_name, event_type, message):
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO security_events (target_name,event_type,message) VALUES (?,?,?)",
            (target_name, event_type, message))
        return cur.lastrowid

def get_all_events():
    with _connect() as conn:
        return [tuple(row) for row in conn.execute(
            "SELECT id,target_name,event_type,message,timestamp FROM security_events ORDER BY id DESC")]

def get_last_evidence_hash():
    with _connect() as conn:
        row = conn.execute("SELECT event_hash FROM evidence_chain ORDER BY id DESC LIMIT 1").fetchone()
        return row["event_hash"] if row else None

def save_evidence_record(payload, previous_hash, event_hash):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO evidence_chain (payload_json,previous_hash,event_hash) VALUES (?,?,?)",
            (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
             previous_hash, event_hash))

def get_evidence_records():
    with _connect() as conn:
        return [tuple(row) for row in conn.execute(
            "SELECT id,payload_json,previous_hash,event_hash FROM evidence_chain ORDER BY id ASC")]

def get_evidence_summary():
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM evidence_chain").fetchone()
        return {"records": row["count"], "database": "SQLite"}
