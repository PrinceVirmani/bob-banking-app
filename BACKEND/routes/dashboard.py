"""
routes/dashboard.py
───────────────────
Blueprint for the main dashboard page.

GET /dashboard → show current balance and recent transactions (login required)
GET /          → redirect root URL to /dashboard
"""
from flask import Blueprint, render_template, session, redirect, url_for, flash
from services.account_service import get_balance, get_recent_transactions
from services.decorators import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    """Root URL — redirect to dashboard (or login if not authenticated)."""
    if session.get("user_id"):
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("auth.login"))


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    user_id   = session["user_id"]
    full_name = session.get("full_name", session.get("username", "Customer"))

    # Fetch balance
    balance_result = get_balance(user_id)
    if not balance_result.ok:
        # Account data is missing — force re-login
        session.clear()
        flash("Your account could not be found. Please contact support.", "danger")
        return redirect(url_for("auth.login"))

    # Fetch recent transactions for the mini-ledger
    txn_result = get_recent_transactions(user_id, limit=5)
    transactions = txn_result.data["transactions"] if txn_result.ok else []

    return render_template(
        "dashboard.html",
        full_name=full_name,
        balance=balance_result.data["balance"],
        transactions=transactions,
    )
