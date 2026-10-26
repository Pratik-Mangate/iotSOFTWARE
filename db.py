"""
Database helper for prediction history.
Uses SQLite for lightweight persistence with base64 image asset storage.
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
    """Create the predictions table and handle schema migrations."""
    conn = _get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            image_file  TEXT    NOT NULL,
            image_data  TEXT,
            predicted   TEXT    NOT NULL,
            confidence  REAL,
            top3        TEXT
        )
        """
    )
    # Check if image_data column exists (for pre-existing databases)
    cursor = conn.execute("PRAGMA table_info(predictions)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "image_data" not in columns:
        try:
            conn.execute("ALTER TABLE predictions ADD COLUMN image_data TEXT")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


def save_prediction(image_file, predicted, confidence, top3_json, image_data=None):
    """Insert a new prediction record and return its primary key ID."""
    conn = _get_connection()
    cursor = conn.execute(
        """
        INSERT INTO predictions (timestamp, image_file, image_data, predicted, confidence, top3)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            image_file,
            image_data or "",
            predicted,
            confidence,
            top3_json,
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_record(record_id):
    """Return a single prediction record by ID, or None."""
    conn = _get_connection()
    row = conn.execute(
        "SELECT * FROM predictions WHERE id = ?",
        (record_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


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
