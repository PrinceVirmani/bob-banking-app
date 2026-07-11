"""
tests/test_auth_service.py
──────────────────────────
Unit tests for services/auth_service.py.
Uses an in-memory SQLite database — the real banking.db is never touched.
"""
import os
import sys
import sqlite3
import unittest
from unittest.mock import patch

# Make BACKEND/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from werkzeug.security import generate_password_hash
from services.auth_service import verify_credentials


# ── Test fixture helpers ──────────────────────────────────────────────────────

def _make_in_memory_db() -> sqlite3.Connection:
    """Create a fresh in-memory database with the users table pre-populated."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name     TEXT NOT NULL DEFAULT ''
        )
    """)
    conn.execute(
        "INSERT INTO users (username, password_hash, full_name) VALUES (?, ?, ?)",
        ("alice", generate_password_hash("password123"), "Alice Johnson"),
    )
    conn.commit()
    return conn


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestVerifyCredentials(unittest.TestCase):

    def setUp(self):
        """Patch get_db to return a fresh in-memory connection for each test."""
        self._conn = _make_in_memory_db()
        self._patcher_get  = patch("services.auth_service.get_db",   return_value=self._conn)
        self._patcher_close = patch("services.auth_service.close_db", return_value=None)
        self._patcher_get.start()
        self._patcher_close.start()

    def tearDown(self):
        self._patcher_get.stop()
        self._patcher_close.stop()
        self._conn.close()

    # ── Success path ──────────────────────────────────────────────────────────

    def test_valid_credentials_return_user_dict(self):
        result = verify_credentials("alice", "password123")
        self.assertIsNotNone(result)
        self.assertEqual(result["username"], "alice")
        self.assertIn("id", result)
        self.assertIn("full_name", result)
        # password_hash must NOT be in the returned dict
        self.assertNotIn("password_hash", result)

    def test_username_is_case_insensitive(self):
        result = verify_credentials("ALICE", "password123")
        self.assertIsNotNone(result)

    # ── Failure paths ─────────────────────────────────────────────────────────

    def test_wrong_password_returns_none(self):
        result = verify_credentials("alice", "wrongpassword")
        self.assertIsNone(result)

    def test_unknown_username_returns_none(self):
        result = verify_credentials("bob", "password123")
        self.assertIsNone(result)

    def test_empty_username_returns_none(self):
        result = verify_credentials("", "password123")
        self.assertIsNone(result)

    def test_empty_password_returns_none(self):
        result = verify_credentials("alice", "")
        self.assertIsNone(result)

    def test_both_empty_returns_none(self):
        result = verify_credentials("", "")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
