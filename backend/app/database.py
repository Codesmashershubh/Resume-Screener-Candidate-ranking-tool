"""
Lightweight SQLite persistence for past screening sessions ("history").

Important: on Render's Free web service instance type, the filesystem is
ephemeral - this database is wiped on every redeploy, restart, or spin-down
(free instances spin down after 15 minutes of inactivity). History will
therefore persist only while the instance stays warm, not durably. This is
a deliberate, documented trade-off (see README.md -> Deployment), not a
bug: it keeps the whole app deployable on a $0 instance with zero external
dependencies. If you need durable history on Render, either attach a
persistent disk on a paid instance and point DATABASE_PATH at it, or swap
this module for Render's free Postgres.

Every function here is best-effort: a storage failure (read-only fs,
missing directory, disk full, corrupted file) is logged and swallowed
rather than raised, so a database hiccup can never break the core
"upload resumes, get ranked results" flow, which doesn't need the DB at all.
"""

from __future__ import annotations
import json
import logging
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from . import config

logger = logging.getLogger("resume_screener.database")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    jd_excerpt TEXT NOT NULL,
    candidate_count INTEGER NOT NULL,
    top_candidate_name TEXT,
    top_candidate_score REAL,
    result_json TEXT NOT NULL
);
"""


@contextmanager
def _connect():
    os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DATABASE_PATH, timeout=5)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> bool:
    """Create the schema if needed. Returns False (without raising) on failure."""
    if not config.ENABLE_HISTORY:
        return False
    try:
        with _connect() as conn:
            conn.execute(_SCHEMA)
        return True
    except Exception:
        logger.warning("Could not initialize history database - history will be disabled.", exc_info=True)
        return False


def save_session(session_id: str, jd_excerpt: str, result: dict) -> str | None:
    """Persist an analysis result. Returns the session id, or None if not saved."""
    if not config.ENABLE_HISTORY:
        return None

    candidates = result.get("candidates", [])
    top = candidates[0] if candidates else None

    try:
        with _connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions "
                "(id, created_at, jd_excerpt, candidate_count, top_candidate_name, top_candidate_score, result_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    result.get("created_at") or datetime.now(timezone.utc).isoformat(),
                    jd_excerpt[:200],
                    len(candidates),
                    top["display_name"] if top else None,
                    top["total_score"] if top else None,
                    json.dumps(result),
                ),
            )
            _prune_old_sessions(conn)
        return session_id
    except Exception:
        logger.warning("Could not save session %s to history.", session_id, exc_info=True)
        return None


def _prune_old_sessions(conn: sqlite3.Connection) -> None:
    conn.execute(
        "DELETE FROM sessions WHERE id NOT IN "
        "(SELECT id FROM sessions ORDER BY created_at DESC LIMIT ?)",
        (config.MAX_STORED_SESSIONS,),
    )


def list_sessions() -> list[dict]:
    if not config.ENABLE_HISTORY:
        return []
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT id, created_at, jd_excerpt, candidate_count, top_candidate_name, top_candidate_score "
                "FROM sessions ORDER BY created_at DESC LIMIT ?",
                (config.MAX_STORED_SESSIONS,),
            ).fetchall()
        return [
            {
                "session_id": r[0],
                "created_at": r[1],
                "jd_excerpt": r[2],
                "candidate_count": r[3],
                "top_candidate_name": r[4],
                "top_candidate_score": r[5],
            }
            for r in rows
        ]
    except Exception:
        logger.warning("Could not read history.", exc_info=True)
        return []


def get_session(session_id: str) -> dict | None:
    if not config.ENABLE_HISTORY:
        return None
    try:
        with _connect() as conn:
            row = conn.execute("SELECT result_json FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return json.loads(row[0]) if row else None
    except Exception:
        logger.warning("Could not read session %s from history.", session_id, exc_info=True)
        return None


def delete_session(session_id: str) -> bool:
    if not config.ENABLE_HISTORY:
        return False
    try:
        with _connect() as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return True
    except Exception:
        logger.warning("Could not delete session %s from history.", session_id, exc_info=True)
        return False
