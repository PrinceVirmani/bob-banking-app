"""
services/account_service.py
────────────────────────────
Account and transaction business logic.
All balance reads and writes pass through this module.
No HTTP, no Flask imports.
"""
from __future__ import annotations

from database.db import get_db, close_db


# ── Result helpers ────────────────────────────────────────────────────────────

class ServiceResult:
    """Lightweight result carrier returned by every service function."""

    __slots__ = ("ok", "data", "error")

    def __init__(self, ok: bool, data=None, error: str = ""):
        self.ok    = ok
        self.data  = data
        self.error = error

    @classmethod
    def success(cls, data=None) -> "ServiceResult":
        return cls(ok=True, data=data)

    @classmethod
    def failure(cls, error: str) -> "ServiceResult":
        return cls(ok=False, error=error)


# ── Public API ────────────────────────────────────────────────────────────────

def get_balance(user_id: int) -> ServiceResult:
    """
    Fetch the current balance for user_id.
    Returns ServiceResult with data={'balance': float} on success.
    """
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT balance FROM accounts WHERE user_id = ?", (user_id,)
        ).fetchone()
    finally:
        close_db(conn)

    if row is None:
        return ServiceResult.failure("Account not found for this user.")

    return ServiceResult.success({"balance": float(row["balance"])})


def deposit(user_id: int, amount: float) -> ServiceResult:
    """
    Add *amount* to the user's balance and record the transaction.

    Validation (performed here, not only in the route):
    - amount must be a positive number greater than 0.
    - A maximum single deposit of 1,000,000 is enforced.
    """
    if not isinstance(amount, (int, float)) or amount <= 0:
        return ServiceResult.failure("Deposit amount must be a positive number.")
    if amount > 1_000_000:
        return ServiceResult.failure("Single deposit cannot exceed $1,000,000.")

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT balance FROM accounts WHERE user_id = ?", (user_id,)
        ).fetchone()

        if row is None:
            return ServiceResult.failure("Account not found.")

        new_balance = float(row["balance"]) + amount

        conn.execute(
            "UPDATE accounts SET balance = ?, updated_at = datetime('now') WHERE user_id = ?",
            (new_balance, user_id),
        )
        conn.execute(
            """INSERT INTO transactions (user_id, tx_type, amount, balance_after)
               VALUES (?, 'deposit', ?, ?)""",
            (user_id, amount, new_balance),
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        return ServiceResult.failure(f"Transaction failed: {exc}")
    finally:
        close_db(conn)

    return ServiceResult.success({"balance": new_balance, "amount": amount})


def withdraw(user_id: int, amount: float) -> ServiceResult:
    """
    Subtract *amount* from the user's balance and record the transaction.

    Validation:
    - amount must be positive.
    - Current balance must be >= amount (no overdraft).
    """
    if not isinstance(amount, (int, float)) or amount <= 0:
        return ServiceResult.failure("Withdrawal amount must be a positive number.")
    if amount > 1_000_000:
        return ServiceResult.failure("Single withdrawal cannot exceed $1,000,000.")

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT balance FROM accounts WHERE user_id = ?", (user_id,)
        ).fetchone()

        if row is None:
            return ServiceResult.failure("Account not found.")

        current_balance = float(row["balance"])

        if current_balance < amount:
            return ServiceResult.failure(
                f"Insufficient funds. Available balance: ${current_balance:,.2f}."
            )

        new_balance = current_balance - amount

        conn.execute(
            "UPDATE accounts SET balance = ?, updated_at = datetime('now') WHERE user_id = ?",
            (new_balance, user_id),
        )
        conn.execute(
            """INSERT INTO transactions (user_id, tx_type, amount, balance_after)
               VALUES (?, 'withdrawal', ?, ?)""",
            (user_id, amount, new_balance),
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        return ServiceResult.failure(f"Transaction failed: {exc}")
    finally:
        close_db(conn)

    return ServiceResult.success({"balance": new_balance, "amount": amount})


def get_recent_transactions(user_id: int, limit: int = 5) -> ServiceResult:
    """Return the most recent *limit* transactions for the dashboard feed."""
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT tx_type, amount, balance_after, created_at
               FROM transactions
               WHERE user_id = ?
               ORDER BY id DESC
               LIMIT ?""",
            (user_id, limit),
        ).fetchall()
    finally:
        close_db(conn)

    txns = [
        {
            "tx_type":      r["tx_type"],
            "amount":       float(r["amount"]),
            "balance_after": float(r["balance_after"]),
            "created_at":   r["created_at"],
        }
        for r in rows
    ]
    return ServiceResult.success({"transactions": txns})
