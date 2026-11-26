import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "data" / "canarytrap.db"

def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def create_database():
    with get_connection() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_name TEXT NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'INFO',
            message TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'dashboard',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        columns = {r["name"] for r in conn.execute("PRAGMA table_info(security_events)")}
        if "severity" not in columns:
            conn.execute("ALTER TABLE security_events ADD COLUMN severity TEXT NOT NULL DEFAULT 'INFO'")
        if "source" not in columns:
            conn.execute("ALTER TABLE security_events ADD COLUMN source TEXT NOT NULL DEFAULT 'dashboard'")

def save_event(target_name, event_type, severity, message, source="dashboard"):
    with get_connection() as conn:
        cur = conn.execute("""INSERT INTO security_events
            (target_name,event_type,severity,message,source) VALUES (?,?,?,?,?)""",
            (target_name,event_type,severity,message,source))
        return cur.lastrowid

def get_all_events(limit=100):
    limit = max(1, min(int(limit), 500))
    with get_connection() as conn:
        rows = conn.execute("""SELECT id,target_name,event_type,severity,message,source,timestamp
            FROM security_events ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()
        return [dict(r) for r in rows]

def get_event_stats():
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM security_events").fetchone()[0]
        decoys = conn.execute("SELECT COUNT(*) FROM security_events WHERE event_type='DECOY_ACCESS'").fetchone()[0]
        critical = conn.execute("SELECT COUNT(*) FROM security_events WHERE severity='CRITICAL'").fetchone()[0]
        high = conn.execute("SELECT COUNT(*) FROM security_events WHERE severity='HIGH'").fetchone()[0]
    return {"total_events": total, "decoy_detections": decoys,
            "critical_events": critical, "high_events": high}
