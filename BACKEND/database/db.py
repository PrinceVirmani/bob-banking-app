"""
database/db.py
──────────────
Single point of contact for all SQLite database connections.
Every service imports get_db() from here; no other file opens sqlite3 directly.
"""
import sqlite3
import os
import sys

# Allow imports when run as a script from BACKEND/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH


def get_db() -> sqlite3.Connection:
    """
    Open and return a SQLite connection configured so that:
    - Rows are accessible as dictionaries (row['column_name']).
    - Foreign key enforcement is enabled.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row          # dict-like row access
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def close_db(conn: sqlite3.Connection) -> None:
    """Close a database connection if it is open."""
    if conn is not None:
        conn.close()
