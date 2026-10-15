"""
database.py
-----------
SQLite storage. The database file is created automatically in backend/database/
the first time the server starts - nothing needs to be installed or set up.

Tables
  access_points    - the Wi-Fi APs (position, capacity, live load)
  users            - the virtual students (position, connected AP, signal)
  simulation_logs  - one row per simulation tick (used for history charts)
"""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from models import DEFAULT_ACCESS_POINTS

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
DB_PATH = os.path.join(DB_DIR, "digital_twin.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS access_points (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    location        TEXT NOT NULL,
    x               REAL NOT NULL,
    y               REAL NOT NULL,
    coverage_range  REAL NOT NULL,
    capacity        INTEGER NOT NULL,
    online          INTEGER NOT NULL DEFAULT 1,
    connected_users INTEGER NOT NULL DEFAULT 0,
    utilization     REAL NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'Normal'
);

CREATE TABLE IF NOT EXISTS users (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    x            REAL NOT NULL,
    y            REAL NOT NULL,
    connected_ap TEXT,
    distance     REAL,
    rssi         INTEGER,
    quality      TEXT,
    status       TEXT
);

CREATE TABLE IF NOT EXISTS simulation_logs (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    tick               INTEGER NOT NULL,
    timestamp          TEXT NOT NULL,
    connected_users    INTEGER,
    disconnected_users INTEGER,
    avg_signal         REAL,
    avg_utilization    REAL,
    congested_aps      INTEGER,
    weak_users         INTEGER,
    ap_loads           TEXT
);
"""


@contextmanager
def get_connection():
    """Open a connection, commit on success, always close."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _insert_default_aps(conn):
    for ap in DEFAULT_ACCESS_POINTS:
        conn.execute(
            "INSERT OR REPLACE INTO access_points "
            "(id, name, location, x, y, coverage_range, capacity, online) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ap["id"], ap["name"], ap["location"], ap["x"], ap["y"],
             ap["coverage_range"], ap["capacity"], ap["online"]),
        )


def init_db():
    """Create the tables if they do not exist and add the 4 default APs."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        count = conn.execute("SELECT COUNT(*) FROM access_points").fetchone()[0]
        if count == 0:
            _insert_default_aps(conn)


def reset_access_points():
    """Restore the original AP layout (used by the Reset button)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM access_points")
        _insert_default_aps(conn)


def load_access_points():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, location, x, y, coverage_range, capacity, online "
            "FROM access_points ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def update_access_point_position(ap_id, x, y):
    with get_connection() as conn:
        conn.execute("UPDATE access_points SET x = ?, y = ? WHERE id = ?", (x, y, ap_id))


def set_access_point_online(ap_id, online):
    with get_connection() as conn:
        conn.execute("UPDATE access_points SET online = ? WHERE id = ?", (1 if online else 0, ap_id))


def save_snapshot(users, aps):
    """Store the current state of every user and the live load of every AP."""
    with get_connection() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO users "
            "(id, name, x, y, connected_ap, distance, rssi, quality, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(u.id, u.name, round(u.x, 1), round(u.y, 1), u.connected_ap,
              u.distance, u.rssi, u.quality, u.status) for u in users],
        )
        conn.executemany(
            "UPDATE access_points SET connected_users = ?, utilization = ?, status = ? WHERE id = ?",
            [(a.connected_users, a.utilization, a.congestion, a.id) for a in aps],
        )


def insert_log(tick, entry, ap_loads):
    """Append one row to simulation_logs."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO simulation_logs (tick, timestamp, connected_users, disconnected_users, "
            "avg_signal, avg_utilization, congested_aps, weak_users, ap_loads) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (tick, datetime.now().isoformat(timespec="seconds"),
             entry["connected_users"], entry["disconnected_users"], entry["avg_signal"],
             entry["avg_utilization"], entry["congested_aps"], entry["weak_users"],
             json.dumps(ap_loads)),
        )


def clear_logs():
    with get_connection() as conn:
        conn.execute("DELETE FROM simulation_logs")


def get_logs(limit=60):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM simulation_logs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    logs = [dict(r) for r in rows][::-1]          # oldest first
    for row in logs:
        row["ap_loads"] = json.loads(row["ap_loads"]) if row["ap_loads"] else {}
    return logs
