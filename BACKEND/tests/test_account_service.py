"""
tests/test_account_service.py
──────────────────────────────
Unit tests for services/account_service.py.
Each test gets its own in-memory database, so tests are fully isolated.
"""
import os
import sys
import sqlite3
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.account_service import get_balance, deposit, withdraw


# ── Fixture ───────────────────────────────────────────────────────────────────

def _make_db(initial_balance: float = 1000.00) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE accounts (
            id         INTEGER PRIMARY KEY,
            user_id    INTEGER NOT NULL UNIQUE,
            balance    REAL    NOT NULL DEFAULT 0,
            updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE transactions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            tx_type      TEXT    NOT NULL,
            amount       REAL    NOT NULL,
            balance_after REAL   NOT NULL,
            created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute(
        "INSERT INTO accounts (user_id, balance) VALUES (1, ?)", (initial_balance,)
    )
    conn.commit()
    return conn


def _patch_db(conn):
    """Return a context-manager pair that patches get_db / close_db."""
    pg = patch("services.account_service.get_db",   return_value=conn)
    pc = patch("services.account_service.close_db", return_value=None)
    return pg, pc


# ── get_balance ───────────────────────────────────────────────────────────────

class TestGetBalance(unittest.TestCase):

    def test_returns_correct_balance(self):
        conn = _make_db(500.00)
        pg, pc = _patch_db(conn)
        with pg, pc:
            result = get_balance(1)
        self.assertTrue(result.ok)
        self.assertAlmostEqual(result.data["balance"], 500.00)
        conn.close()

    def test_unknown_user_returns_failure(self):
        conn = _make_db()
        pg, pc = _patch_db(conn)
        with pg, pc:
            result = get_balance(999)
        self.assertFalse(result.ok)
        self.assertIn("not found", result.error.lower())
        conn.close()


# ── deposit ───────────────────────────────────────────────────────────────────

class TestDeposit(unittest.TestCase):

    def _run(self, user_id, amount, balance=1000.00):
        conn = _make_db(balance)
        pg, pc = _patch_db(conn)
        with pg, pc:
            result = deposit(user_id, amount)
        return result, conn

    def test_deposit_increases_balance(self):
        result, conn = self._run(1, 250.00)
        self.assertTrue(result.ok)
        self.assertAlmostEqual(result.data["balance"], 1250.00)
        conn.close()

    def test_deposit_records_transaction(self):
        result, conn = self._run(1, 100.00)
        row = conn.execute("SELECT * FROM transactions WHERE user_id = 1").fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["tx_type"], "deposit")
        self.assertAlmostEqual(row["amount"], 100.00)
        conn.close()

    def test_zero_amount_rejected(self):
        result, conn = self._run(1, 0)
        self.assertFalse(result.ok)
        conn.close()

    def test_negative_amount_rejected(self):
        result, conn = self._run(1, -50)
        self.assertFalse(result.ok)
        conn.close()

    def test_exceeding_max_rejected(self):
        result, conn = self._run(1, 2_000_000)
        self.assertFalse(result.ok)
        conn.close()


# ── withdraw ──────────────────────────────────────────────────────────────────

class TestWithdraw(unittest.TestCase):

    def _run(self, user_id, amount, balance=1000.00):
        conn = _make_db(balance)
        pg, pc = _patch_db(conn)
        with pg, pc:
            result = withdraw(user_id, amount)
        return result, conn

    def test_valid_withdrawal_decreases_balance(self):
        result, conn = self._run(1, 300.00)
        self.assertTrue(result.ok)
        self.assertAlmostEqual(result.data["balance"], 700.00)
        conn.close()

    def test_withdrawal_records_transaction(self):
        result, conn = self._run(1, 100.00)
        row = conn.execute("SELECT * FROM transactions WHERE user_id = 1").fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["tx_type"], "withdrawal")
        conn.close()

    def test_insufficient_funds_rejected(self):
        result, conn = self._run(1, 1500.00, balance=1000.00)
        self.assertFalse(result.ok)
        self.assertIn("insufficient", result.error.lower())
        conn.close()

    def test_exact_balance_withdrawal_succeeds(self):
        result, conn = self._run(1, 1000.00, balance=1000.00)
        self.assertTrue(result.ok)
        self.assertAlmostEqual(result.data["balance"], 0.00)
        conn.close()

    def test_zero_amount_rejected(self):
        result, conn = self._run(1, 0)
        self.assertFalse(result.ok)
        conn.close()

    def test_negative_amount_rejected(self):
        result, conn = self._run(1, -100)
        self.assertFalse(result.ok)
        conn.close()


if __name__ == "__main__":
    unittest.main()
