# ai-generated: 90% - Claude Code drafted this; the author reviewed the schema and persistence choice (R-23)
"""SQLite-backed ticket storage. A named volume (docker-compose.yml) keeps /data across restarts (R-23)."""
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from .config import DB_PATH


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            reporter_name TEXT NOT NULL,
            reporter_email TEXT,
            reporter_vip INTEGER NOT NULL,
            impact INTEGER NOT NULL,
            urgency INTEGER NOT NULL,
            priority TEXT NOT NULL,
            state TEXT NOT NULL,
            created_at TEXT NOT NULL,
            acknowledged_at TEXT,
            resolved_at TEXT,
            closed_at TEXT,
            related_to TEXT,
            ack_due_at TEXT NOT NULL,
            resolve_due_at TEXT NOT NULL,
            resolve_clock TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def _fmt(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat()


def _parse(s: Optional[str]) -> Optional[datetime]:
    if s is None:
        return None
    return datetime.fromisoformat(s)


def _row_to_ticket(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "reporter": {
            "name": row["reporter_name"],
            "email": row["reporter_email"],
            "vip": bool(row["reporter_vip"]),
        },
        "impact": row["impact"],
        "urgency": row["urgency"],
        "priority": row["priority"],
        "state": row["state"],
        "created_at": _parse(row["created_at"]),
        "acknowledged_at": _parse(row["acknowledged_at"]),
        "resolved_at": _parse(row["resolved_at"]),
        "closed_at": _parse(row["closed_at"]),
        "related_to": row["related_to"],
        "ack_due_at": _parse(row["ack_due_at"]),
        "resolve_due_at": _parse(row["resolve_due_at"]),
        "resolve_clock": row["resolve_clock"],
    }


def insert(t: dict) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO tickets (
            id, title, description, reporter_name, reporter_email, reporter_vip,
            impact, urgency, priority, state, created_at, acknowledged_at, resolved_at,
            closed_at, related_to, ack_due_at, resolve_due_at, resolve_clock
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            t["id"], t["title"], t["description"],
            t["reporter"]["name"], t["reporter"]["email"], int(t["reporter"]["vip"]),
            t["impact"], t["urgency"], t["priority"], t["state"],
            _fmt(t["created_at"]), _fmt(t["acknowledged_at"]), _fmt(t["resolved_at"]),
            _fmt(t["closed_at"]), t["related_to"], _fmt(t["ack_due_at"]), _fmt(t["resolve_due_at"]),
            t["resolve_clock"],
        ),
    )
    conn.commit()
    conn.close()


def get(ticket_id: str) -> Optional[dict]:
    conn = _connect()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return _row_to_ticket(row) if row else None


def list_tickets(state: Optional[str] = None, priority: Optional[str] = None) -> list[dict]:
    conn = _connect()
    query = "SELECT * FROM tickets WHERE 1 = 1"
    params: list[str] = []
    if state:
        query += " AND state = ?"
        params.append(state)
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_row_to_ticket(r) for r in rows]


def update(t: dict) -> None:
    conn = _connect()
    conn.execute(
        "UPDATE tickets SET state = ?, acknowledged_at = ?, resolved_at = ?, closed_at = ? WHERE id = ?",
        (t["state"], _fmt(t["acknowledged_at"]), _fmt(t["resolved_at"]), _fmt(t["closed_at"]), t["id"]),
    )
    conn.commit()
    conn.close()
