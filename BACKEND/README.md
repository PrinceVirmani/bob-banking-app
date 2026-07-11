# SecureBank — Banking Web Application

A lightweight full-stack banking application built with **HTML + Bootstrap**,
**Python Flask**, and **SQLite**.

---

## Quick Start

```bash
# 1. Navigate into the backend
cd BACKEND

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app  (database is auto-initialised on first start)
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

**Demo credentials:** `alice` / `password123` (starting balance: $2,500.00)

---

## Run Tests

```bash
cd BACKEND
source venv/bin/activate
pip install pytest          # one-time
python -m pytest tests/ -v
```

Expected output: **39 passed**

---

## Project Structure

```
banking-workshop/
├── IMPLEMENTATION_PLAN.md              ← Architecture & planning document
├── STEP_BY_STEP_IMPLEMENTATION_GUIDE.md← Plain-English build guide
│
├── FRONTEND/
│   ├── templates/
│   │   ├── base.html                   ← Shared layout (navbar, flash alerts)
│   │   ├── login.html                  ← Login page
│   │   ├── dashboard.html              ← Balance overview + recent transactions
│   │   ├── deposit.html                ← Deposit form
│   │   └── withdraw.html               ← Withdrawal form
│   └── static/css/
│       └── custom.css                  ← Minor Bootstrap overrides
│
└── BACKEND/
    ├── app.py                          ← Flask entry point & blueprint registration
    ├── config.py                       ← Settings (secret key, DB path, debug flag)
    ├── requirements.txt
    ├── banking.db                      ← SQLite database (auto-created)
    ├── database/
    │   ├── db.py                       ← Connection helper (get_db / close_db)
    │   └── init_db.py                  ← Schema creation + seed data script
    ├── services/
    │   ├── auth_service.py             ← Credential verification (hash-safe)
    │   ├── account_service.py          ← Balance, deposit, withdrawal logic
    │   └── decorators.py               ← @login_required decorator
    ├── routes/
    │   ├── auth.py                     ← /login  /logout
    │   ├── dashboard.py                ← /  /dashboard
    │   └── transactions.py             ← /deposit  /withdraw
    └── tests/
        ├── test_auth_service.py        ← Unit tests: auth service (7 tests)
        ├── test_account_service.py     ← Unit tests: account service (13 tests)
        └── test_routes.py              ← Integration tests: all routes (19 tests)
```

---

## Features

| Feature | URL | Auth Required |
|---|---|---|
| Login | `GET/POST /login` | No |
| Logout | `GET /logout` | No |
| Dashboard + Balance | `GET /dashboard` | ✓ |
| Deposit Funds | `GET/POST /deposit` | ✓ |
| Withdraw Funds | `GET/POST /withdraw` | ✓ |

---

## Security Notes

- Passwords are stored as bcrypt hashes via Werkzeug — never plaintext.
- All protected routes require a valid server-side session (`@login_required`).
- Login error messages are generic — "Invalid username or password" regardless of which field failed.
- Session is invalidated on logout (`session.clear()`).
- All SQL queries use parameterised placeholders — no string formatting.
- `SECRET_KEY` and `DATABASE_PATH` can be overridden via environment variables for production.

---

## Production Checklist

- [ ] Set `SECRET_KEY` environment variable to a 32+ character random string
- [ ] Set `FLASK_DEBUG=false`
- [ ] Run with Gunicorn: `gunicorn -w 2 app:app`
- [ ] Serve behind Nginx with HTTPS enabled
- [ ] Remove or change the seed user password
