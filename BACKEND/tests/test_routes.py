"""
tests/test_routes.py
────────────────────
Integration tests for Flask routes.
Uses Flask's test client + a temporary SQLite database so no real data is touched.
"""
import os
import sys
import sqlite3
import tempfile
import unittest

# Make BACKEND/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from werkzeug.security import generate_password_hash


# ── Helpers ───────────────────────────────────────────────────────────────────

def _seed_temp_db(db_path: str) -> None:
    """Create tables and insert one test user into the temporary database."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
            balance REAL NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tx_type TEXT NOT NULL,
            amount REAL NOT NULL,
            balance_after REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute(
        "INSERT INTO users (username, password_hash, full_name) VALUES (?, ?, ?)",
        ("testuser", generate_password_hash("testpass"), "Test User"),
    )
    conn.execute("INSERT INTO accounts (user_id, balance) VALUES (1, 1000.00)")
    conn.commit()
    conn.close()


def _build_app(db_path: str):
    """
    Build a fresh Flask app instance pointing at *db_path*.
    Import config and app fresh each time so the DATABASE_PATH is applied
    before any connection is opened.
    """
    import config
    config.DATABASE_PATH = db_path

    # Force re-import of database.db so it picks up the new DATABASE_PATH
    import importlib
    import database.db
    importlib.reload(database.db)

    from app import create_app
    flask_app = create_app()
    flask_app.config.update(
        TESTING=True,
        DEBUG=False,
        SECRET_KEY="test-secret-key-32-characters!!",
    )
    return flask_app


# ── Base test case ─────────────────────────────────────────────────────────────

class BaseRouteTest(unittest.TestCase):

    def setUp(self):
        self._db_fd, self._db_path = tempfile.mkstemp(suffix=".db")
        _seed_temp_db(self._db_path)

        self.app    = _build_app(self._db_path)
        # Use a persistent cookie jar so session survives across requests
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        os.close(self._db_fd)
        os.unlink(self._db_path)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _login(self, username="testuser", password="testpass"):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def _logout(self):
        return self.client.get("/logout", follow_redirects=True)


# ── Authentication tests ───────────────────────────────────────────────────────

class TestAuthRoutes(BaseRouteTest):

    def test_login_page_loads(self):
        r = self.client.get("/login")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Sign In", r.data)

    def test_valid_login_redirects_to_dashboard(self):
        r = self._login()
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Dashboard", r.data)

    def test_invalid_password_shows_error(self):
        r = self.client.post(
            "/login",
            data={"username": "testuser", "password": "wrong"},
            follow_redirects=True,
        )
        self.assertIn(b"Invalid username or password", r.data)

    def test_unknown_user_shows_error(self):
        r = self.client.post(
            "/login",
            data={"username": "nobody", "password": "testpass"},
            follow_redirects=True,
        )
        self.assertIn(b"Invalid username or password", r.data)

    def test_logout_redirects_to_login(self):
        self._login()
        r = self._logout()
        self.assertIn(b"Sign In", r.data)

    def test_empty_username_shows_error(self):
        r = self.client.post(
            "/login",
            data={"username": "", "password": "testpass"},
            follow_redirects=True,
        )
        self.assertIn(b"Please enter your username", r.data)


# ── Dashboard tests ────────────────────────────────────────────────────────────

class TestDashboardRoute(BaseRouteTest):

    def test_dashboard_requires_login(self):
        r = self.client.get("/dashboard", follow_redirects=True)
        self.assertIn(b"Sign In", r.data)

    def test_dashboard_shows_balance_after_login(self):
        self._login()
        r = self.client.get("/dashboard")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"1,000.00", r.data)

    def test_root_redirects_to_dashboard_when_logged_in(self):
        self._login()
        r = self.client.get("/", follow_redirects=True)
        self.assertIn(b"Dashboard", r.data)


# ── Deposit tests ──────────────────────────────────────────────────────────────

class TestDepositRoute(BaseRouteTest):

    def test_deposit_page_requires_login(self):
        r = self.client.get("/deposit", follow_redirects=True)
        self.assertIn(b"Sign In", r.data)

    def test_valid_deposit_redirects_with_success(self):
        self._login()
        r = self.client.post(
            "/deposit",
            data={"amount": "500"},
            follow_redirects=True,
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"successful", r.data.lower())

    def test_deposit_updates_balance(self):
        self._login()
        self.client.post("/deposit", data={"amount": "200"}, follow_redirects=True)
        r = self.client.get("/dashboard")
        self.assertIn(b"1,200.00", r.data)

    def test_zero_deposit_shows_error(self):
        self._login()
        r = self.client.post("/deposit", data={"amount": "0"}, follow_redirects=True)
        self.assertIn(b"greater than zero", r.data.lower())

    def test_empty_deposit_shows_error(self):
        self._login()
        r = self.client.post("/deposit", data={"amount": ""}, follow_redirects=True)
        self.assertIn(b"enter an amount", r.data.lower())


# ── Withdraw tests ─────────────────────────────────────────────────────────────

class TestWithdrawRoute(BaseRouteTest):

    def test_withdraw_page_requires_login(self):
        r = self.client.get("/withdraw", follow_redirects=True)
        self.assertIn(b"Sign In", r.data)

    def test_valid_withdrawal_redirects_with_success(self):
        self._login()
        r = self.client.post(
            "/withdraw",
            data={"amount": "300"},
            follow_redirects=True,
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"successful", r.data.lower())

    def test_withdrawal_updates_balance(self):
        self._login()
        self.client.post("/withdraw", data={"amount": "400"}, follow_redirects=True)
        r = self.client.get("/dashboard")
        self.assertIn(b"600.00", r.data)

    def test_insufficient_funds_shows_error(self):
        self._login()
        r = self.client.post(
            "/withdraw",
            data={"amount": "9999"},
            follow_redirects=True,
        )
        self.assertIn(b"insufficient", r.data.lower())

    def test_zero_withdrawal_shows_error(self):
        self._login()
        r = self.client.post("/withdraw", data={"amount": "0"}, follow_redirects=True)
        self.assertIn(b"greater than zero", r.data.lower())


if __name__ == "__main__":
    unittest.main()
