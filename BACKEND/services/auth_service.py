"""
services/auth_service.py
────────────────────────
Authentication business logic: credential verification only.
No HTTP, no Flask imports — pure Python so it is trivially testable.
"""
from werkzeug.security import check_password_hash

from database.db import get_db, close_db


def verify_credentials(username: str, password: str) -> dict | None:
    """
    Verify a username / password pair against the database.

    Returns the user row dict  { id, username, full_name, … }  on success.
    Returns None on failure (unknown user OR wrong password).

    Security note: the same return value is used for both failure modes so
    callers cannot distinguish "user not found" from "wrong password" — this
    prevents user-enumeration attacks.
    """
    if not username or not password:
        return None

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, username, password_hash, full_name FROM users WHERE username = ?",
            (username.strip().lower(),),
        ).fetchone()
    finally:
        close_db(conn)

    if row is None:
        return None

    if not check_password_hash(row["password_hash"], password):
        return None

    # Return a plain dict (not a sqlite3.Row) so it's safe to store in session
    return {
        "id":        row["id"],
        "username":  row["username"],
        "full_name": row["full_name"],
    }
