"""
Centralized configuration, read from environment variables.

Every value here has a sensible local-dev default so `uvicorn app.main:app`
works with zero configuration. In production (e.g. Render), override via
the platform's environment variable settings - no code changes needed.
"""

from __future__ import annotations
import os

# Render sets PORT itself (default 10000); locally we default to 8000.
PORT = int(os.environ.get("PORT", "8000"))
HOST = "0.0.0.0"

# Comma-separated list of origins allowed to call this API, e.g.
# "https://my-frontend.onrender.com,http://localhost:5173"
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()
]

# SQLite file path. On Render's Free instance type this directory is
# ephemeral (wiped on every redeploy/restart/spin-down) - see database.py
# and the README's Deployment section for what that means in practice.
DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "screening.db"))

# Whether to persist analysis results to SQLite at all. Defaults on, but
# can be turned off entirely (e.g. if you'd rather not store any resume
# data server-side, even transiently on a warm instance).
ENABLE_HISTORY = os.environ.get("ENABLE_HISTORY", "true").lower() not in ("false", "0", "no")

# How many past sessions to keep before pruning the oldest (keeps the
# ephemeral, unbounded-growth-prone SQLite file small and fast).
MAX_STORED_SESSIONS = int(os.environ.get("MAX_STORED_SESSIONS", "50"))
