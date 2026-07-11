"""
services/decorators.py
───────────────────────
Shared Flask route decorators.
Import login_required and apply it to every route that requires authentication.
"""
from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """
    Route decorator that blocks unauthenticated access.

    If a valid user_id is present in the Flask session the wrapped route
    runs normally.  Otherwise the user is redirected to /login with an
    informational flash message.

    Usage:
        @dashboard_bp.route('/dashboard')
        @login_required
        def dashboard():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please log in to access that page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated
