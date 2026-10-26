"""
Database helper for prediction history.
Uses SQLite for lightweight local persistence.
"""
import os
import sqlite3
from datetime import datetime, timezone

import config


def _get_connection():
    """Return a new connection to the history database."""
    os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create the predictions table if it does not exist."""
    conn = _get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            image_file  TEXT    NOT NULL,
            predicted   TEXT    NOT NULL,
            confidence  REAL,
            top3        TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_prediction(image_file, predicted, confidence, top3_json):
    """Insert a new prediction record."""
    conn = _get_connection()
    conn.execute(
        """
        INSERT INTO predictions (timestamp, image_file, predicted, confidence, top3)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            image_file,
            predicted,
            confidence,
            top3_json,
        ),
    )
    conn.commit()
    conn.close()


def get_history():
    """Return all prediction records, most recent first."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM predictions ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_history():
    """Delete all prediction records."""
    conn = _get_connection()
    conn.execute("DELETE FROM predictions")
    conn.commit()
    conn.close()
