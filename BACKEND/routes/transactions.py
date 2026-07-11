"""
routes/transactions.py
──────────────────────
Blueprint for deposit and withdrawal routes.

GET  /deposit   → render deposit form
POST /deposit   → validate, call service, redirect with result

GET  /withdraw  → render withdraw form
POST /withdraw  → validate, call service, redirect with result
"""
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from services.account_service import deposit, withdraw
from services.decorators import login_required

transactions_bp = Blueprint("transactions", __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_amount(raw: str) -> tuple[float | None, str]:
    """
    Convert raw form string to a float.
    Returns (float, '') on success or (None, error_message) on failure.
    """
    if not raw or raw.strip() == "":
        return None, "Amount is required"
    try:
        value = float(raw.strip())
    except ValueError:
        return None, "Amount must be greater than zero"
    if value <= 0:
        return None, "Amount must be greater than zero"
    return value, ""


# ── Deposit ───────────────────────────────────────────────────────────────────

@transactions_bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit_funds():
    if request.method == "GET":
        return render_template("deposit.html")

    raw    = request.form.get("amount", "")
    amount, parse_error = _parse_amount(raw)

    if parse_error:
        return render_template("deposit.html", error=parse_error, amount=raw)

    result = deposit(session["user_id"], amount)

    if not result.ok:
        return render_template("deposit.html", error=result.error, amount=raw)

    flash(
        f"Deposit of ${amount:,.2f} successful. "
        f"New balance: ${result.data['balance']:,.2f}.",
        "success",
    )
    return redirect(url_for("dashboard.dashboard"))


# ── Withdraw ──────────────────────────────────────────────────────────────────

@transactions_bp.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw_funds():
    if request.method == "GET":
        return render_template("withdraw.html")

    raw = request.form.get("amount", "")

    # Validation checks 1 & 2: empty field and non-positive number.
    # Uses the shared _parse_amount helper for consistency with deposit.
    amount, parse_error = _parse_amount(raw)
    if parse_error:
        return render_template("withdraw.html", error=parse_error, amount=raw)

    # Call the service — it performs the balance check atomically inside a
    # single SQLite transaction, preventing any TOCTOU race condition.
    # Insufficient funds is returned as result.error when balance < amount.
    result = withdraw(session["user_id"], amount)

    if not result.ok:
        return render_template("withdraw.html", error=result.error, amount=raw)

    flash(
        f"Withdrawal of ${amount:,.2f} successful. "
        f"New balance: ${result.data['balance']:,.2f}.",
        "success",
    )
    return redirect(url_for("dashboard.dashboard"))
