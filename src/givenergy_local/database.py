import sqlite3
from pathlib import Path

APP_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    inverter_serial TEXT,
    timestamp   TEXT,
    event_type  TEXT,
    description TEXT,
    cleared_at  TEXT,
    data        JSON
);

CREATE TABLE IF NOT EXISTS settings_map (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_id      TEXT NOT NULL,
    model           TEXT NOT NULL,
    name            TEXT,
    register_type   TEXT,
    register_index  INTEGER,
    data_type       TEXT,
    validation      TEXT,
    UNIQUE (setting_id, model)
);

CREATE TABLE IF NOT EXISTS api_tokens (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT,
    token_hash   TEXT UNIQUE NOT NULL,
    created_at   TEXT DEFAULT (datetime('now')),
    last_used_at TEXT
);

CREATE TABLE IF NOT EXISTS inverters (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    serial              TEXT UNIQUE NOT NULL,
    host                TEXT,
    port                INTEGER DEFAULT 8899,
    site_id             TEXT,
    detected_model      TEXT,
    detected_generation TEXT,
    last_seen           TEXT,
    config              JSON
);

CREATE TABLE IF NOT EXISTS preset_profiles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    inverter_serial TEXT,
    name            TEXT,
    settings        JSON,
    created_at      TEXT DEFAULT (datetime('now'))
);
"""


def init_app_db(db_path: str, check_same_thread: bool = False) -> sqlite3.Connection:
    """Create (or open) the app database, apply schema, and return the connection."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=check_same_thread)
    conn.executescript(APP_SCHEMA)
    conn.commit()
    return conn
