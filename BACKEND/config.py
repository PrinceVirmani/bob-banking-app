import os

# Base directory of the BACKEND package
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "banking.db"),
)

# ── Security ──────────────────────────────────────────────────────────────────
# In production load this from an environment variable; never hard-code.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production-32ch")

# ── Flask ─────────────────────────────────────────────────────────────────────
DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"

# Session expires after 30 minutes of inactivity
SESSION_LIFETIME_MINUTES = 30
