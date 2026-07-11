"""
database/init_db.py
───────────────────
One-time setup script: creates all tables and inserts one seed customer.

Run once from the BACKEND/ folder:
    python database/init_db.py

Re-running is safe — tables are created with IF NOT EXISTS and the seed
insert is skipped when the username already exists.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash
from database.db import get_db, close_db

# ── DDL ───────────────────────────────────────────────────────────────────────

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    full_name     TEXT    NOT NULL DEFAULT '',
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_ACCOUNTS = """
CREATE TABLE IF NOT EXISTS accounts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL UNIQUE REFERENCES users(id),
    balance    REAL    NOT NULL DEFAULT 0.00,
    updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_TRANSACTIONS = """
CREATE TABLE IF NOT EXISTS transactions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    tx_type      TEXT    NOT NULL CHECK(tx_type IN ('deposit', 'withdrawal')),
    amount       REAL    NOT NULL,
    balance_after REAL   NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

# ── Seed data ─────────────────────────────────────────────────────────────────

SEED_USERNAME  = "alice"
SEED_PASSWORD  = "password123"   # Change immediately in production
SEED_FULL_NAME = "Alice Johnson"
SEED_BALANCE   = 2500.00


def init_db() -> None:
    conn = get_db()
    try:
        cur = conn.cursor()

        # Create tables
        cur.execute(CREATE_USERS)
        cur.execute(CREATE_ACCOUNTS)
        cur.execute(CREATE_TRANSACTIONS)

        # Insert seed user only if not already present
        existing = cur.execute(
            "SELECT id FROM users WHERE username = ?", (SEED_USERNAME,)
        ).fetchone()

        if existing is None:
            hashed = generate_password_hash(SEED_PASSWORD)
            cur.execute(
                "INSERT INTO users (username, password_hash, full_name) VALUES (?, ?, ?)",
                (SEED_USERNAME, hashed, SEED_FULL_NAME),
            )
            user_id = cur.lastrowid
            cur.execute(
                "INSERT INTO accounts (user_id, balance) VALUES (?, ?)",
                (user_id, SEED_BALANCE),
            )
            print(f"[init_db] Seed user '{SEED_USERNAME}' created "
                  f"(password: '{SEED_PASSWORD}', balance: ${SEED_BALANCE:,.2f}).")
        else:
            print(f"[init_db] Seed user '{SEED_USERNAME}' already exists — skipped.")

        conn.commit()
        print("[init_db] Database initialised successfully.")
    finally:
        close_db(conn)


if __name__ == "__main__":
    init_db()
