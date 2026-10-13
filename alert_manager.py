import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "outputs" / "incidents.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

EVENT_SEVERITIES = {
    "SYSTEM_NORMAL": "INFO",
    "PERSON_DETECTED": "INFO",
    "SAFETY_LINE_CROSSING": "WARNING",
    "PERSON_ON_TRACK": "DANGER",
    "OBSTACLE_DETECTED": "WARNING",
}

def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _initialize_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                object_id TEXT,
                source TEXT NOT NULL,
                event_key TEXT NOT NULL
            )
        """)

def normalize_event(event):
    if not isinstance(event, dict):
        raise ValueError("Event must be a JSON object.")

    event_type = str(event.get("event_type", "")).strip().upper()
    if event_type not in EVENT_SEVERITIES:
        raise ValueError(f"Unsupported event type: {event_type}")

    severity = str(
        event.get("severity", EVENT_SEVERITIES[event_type])
    ).strip().upper()

    if severity not in {"INFO", "WARNING", "DANGER"}:
        raise ValueError(f"Unsupported severity: {severity}")

    return {
        "event_type": event_type,
        "severity": severity,
        "message": str(event.get("message", event_type)),
        "timestamp": str(
            event.get("timestamp")
            or datetime.now(timezone.utc).isoformat(timespec="seconds")
        ),
        "object_id": str(event.get("object_id", "unknown")),
        "source": str(event.get("source", "unspecified")),
        "event_key": "|".join([
            event_type,
            str(event.get("object_id", "unknown")),
            str(event.get("source", "unspecified")),
        ]),
    }

def add_event(event, cooldown_seconds=15):
    item = normalize_event(event)
    now = datetime.now(timezone.utc)

    with _connect() as conn:
        previous = conn.execute(
            "SELECT timestamp FROM incidents WHERE event_key=? ORDER BY id DESC LIMIT 1",
            (item["event_key"],),
        ).fetchone()

        if previous:
            try:
                old = datetime.fromisoformat(
                    previous["timestamp"].replace("Z", "+00:00")
                )
                if old.tzinfo is None:
                    old = old.replace(tzinfo=timezone.utc)
                if (now - old).total_seconds() < cooldown_seconds:
                    return False, "Duplicate suppressed"
            except ValueError:
                pass

        conn.execute("""
            INSERT INTO incidents
            (event_type, severity, message, timestamp, object_id, source, event_key)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item["event_type"], item["severity"], item["message"],
            item["timestamp"], item["object_id"], item["source"],
            item["event_key"],
        ))

    return True, "Event recorded"

def get_events(limit=500):
    with _connect() as conn:
        rows = conn.execute(
            """SELECT id, event_type, severity, message, timestamp, object_id, source
               FROM incidents ORDER BY id DESC LIMIT ?""",
            (max(1, int(limit)),),
        ).fetchall()
    return [dict(row) for row in rows]

def clear_events():
    with _connect() as conn:
        conn.execute("DELETE FROM incidents")

def process_event_payload(payload, cooldown_seconds=15):
    events = payload if isinstance(payload, list) else [payload]
    inserted = duplicates = 0

    for event in events:
        added, _ = add_event(event, cooldown_seconds)
        if added:
            inserted += 1
        else:
            duplicates += 1

    return {"inserted": inserted, "duplicates": duplicates}

_initialize_db()
