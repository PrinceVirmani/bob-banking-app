"""
app.py
──────
Flask application factory and entry point.

Run locally:
    cd BACKEND
    python app.py

Or with the Flask CLI:
    cd BACKEND
    flask --app app run --debug
"""
import os
import sys
from datetime import timedelta

from flask import Flask

# ── Resolve paths ─────────────────────────────────────────────────────────────
# BACKEND/ is the root; FRONTEND/ lives one level up.
BACKEND_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "FRONTEND", "templates")
STATIC_DIR   = os.path.join(PROJECT_ROOT, "FRONTEND", "static")

# Make BACKEND/ importable (services, routes, database, config)
sys.path.insert(0, BACKEND_DIR)

from config import SECRET_KEY, DEBUG, SESSION_LIFETIME_MINUTES

# ── Application factory ───────────────────────────────────────────────────────

def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=TEMPLATE_DIR,
        static_folder=STATIC_DIR,
    )

    # ── Configuration ─────────────────────────────────────────────────────────
    app.config["SECRET_KEY"]                = SECRET_KEY
    app.config["DEBUG"]                     = DEBUG
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=SESSION_LIFETIME_MINUTES)

    # ── Register blueprints ───────────────────────────────────────────────────
    from routes.auth         import auth_bp
    from routes.dashboard    import dashboard_bp
    from routes.transactions import transactions_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)

    return app


# ── Dev server entry point ────────────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    # Ensure the database exists before starting
    from database.init_db import init_db
    init_db()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=DEBUG,
    )
