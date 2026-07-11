"""
routes/auth.py
──────────────
Blueprint for authentication routes: /login and /logout.

GET  /login  → render login form
POST /login  → validate credentials, create session, redirect to dashboard
GET  /logout → clear session, redirect to login
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
from services.auth_service import verify_credentials

auth_bp = Blueprint("auth", __name__)


# ── /login ────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Already logged in — bounce straight to dashboard
    if session.get("user_id"):
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "GET":
        return render_template("login.html")

    # ── POST: validate inputs ─────────────────────────────────────────────────
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username:
        return render_template("login.html", error="Please enter your username.")
    if not password:
        return render_template("login.html", error="Please enter your password.")

    # ── Authenticate ──────────────────────────────────────────────────────────
    user = verify_credentials(username, password)

    if user is None:
        # Deliberate generic message — do not reveal which field was wrong
        return render_template("login.html", error="Invalid username or password.")

    # ── Success: create session ───────────────────────────────────────────────
    session.clear()                         # guard against session fixation
    session["user_id"]   = user["id"]
    session["username"]  = user["username"]
    session["full_name"] = user["full_name"]
    session.permanent    = True             # respect PERMANENT_SESSION_LIFETIME

    flash(f"Welcome back, {user['full_name'].split()[0]}!", "success")
    return redirect(url_for("dashboard.dashboard"))


# ── /logout ───────────────────────────────────────────────────────────────────

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
