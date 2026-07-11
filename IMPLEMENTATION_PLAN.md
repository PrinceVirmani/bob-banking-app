# Banking Web Application — Implementation Plan

> **Document Type:** High-Level Planning  
> **Status:** Draft  
> **Stack:** HTML + Bootstrap · Python Flask · SQLite

---

## 1. Solution Overview

### Objective

Deliver a lightweight, browser-based banking application that allows customers to securely log in, view their account balance, and perform basic fund transactions (deposit and withdrawal) through a clean web interface.

### Scope

| In Scope | Out of Scope |
|---|---|
| Customer login / logout | Admin portal |
| View account balance | Multi-currency support |
| Deposit funds | External payment integrations |
| Withdraw funds | Mobile native apps |
| Session-based authentication | Multi-factor authentication |

### Users

- **Customer** — an individual account holder who authenticates and manages their own account balance.

### Functional Requirements

1. A customer must be able to log in using a username and password.
2. A logged-in customer must see a dashboard summarising their account.
3. A customer must be able to view their current account balance.
4. A customer must be able to deposit a positive monetary amount into their account.
5. A customer must be able to withdraw a positive monetary amount, subject to sufficient balance.
6. A customer must be able to log out, terminating their session.

### Non-Functional Requirements

| Category | Requirement |
|---|---|
| Security | Passwords stored as hashed values; session tokens server-managed |
| Usability | Responsive UI usable on desktop and tablet via Bootstrap |
| Reliability | Transactions must not leave the account in an inconsistent state |
| Maintainability | Clear separation of frontend, backend, and data layers |
| Performance | Page responses under 1 second for typical single-user local use |

### Assumptions

- Single-user deployment (local or LAN); no horizontal scaling required at this stage.
- One account per customer; no joint or savings account variants.
- SQLite is sufficient for the expected data volume and concurrency level.
- Bootstrap is loaded via CDN; no custom CSS build pipeline is needed.
- Python 3.10+ and Flask are available in the target environment.

---

## 2. High-Level Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        BROWSER                              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │               FRONTEND  (FRONTEND/)                  │  │
│  │                                                      │  │
│  │   HTML Pages          Bootstrap Components           │  │
│  │   login.html          Navbar, Cards, Forms           │  │
│  │   dashboard.html      Alerts, Buttons                │  │
│  │   deposit.html                                       │  │
│  │   withdraw.html                                      │  │
│  └──────────────────┬───────────────────────────────────┘  │
└─────────────────────│───────────────────────────────────────┘
                      │  HTTP Requests (form POST / GET)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND  (BACKEND/)                      │
│                                                             │
│  ┌─────────────┐  ┌───────────────┐  ┌──────────────────┐  │
│  │   Routes    │  │   Services    │  │   Session Mgmt   │  │
│  │  (Flask)    │→ │  (Business    │→ │  (Flask session) │  │
│  │             │  │   Logic)      │  │                  │  │
│  └─────────────┘  └───────┬───────┘  └──────────────────┘  │
└──────────────────────────-│─────────────────────────────────┘
                             │  SQL queries via sqlite3 / ORM
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE  (BACKEND/)                     │
│                                                             │
│                      SQLite File                            │
│                    banking.db                               │
│                                                             │
│           Users table · Accounts table                      │
│           Transactions table                                │
└─────────────────────────────────────────────────────────────┘
```

### Frontend → Backend → Database Interaction

```
Frontend (HTML form)
      │
      │  HTTP POST/GET (form data or query params)
      ▼
Flask Route Handler
      │
      │  Calls service / helper function
      ▼
Business Logic Layer
      │
      │  Reads / writes via database module
      ▼
SQLite Database
      │
      │  Returns result set or row count
      ▼
Business Logic Layer
      │
      │  Returns processed data to route
      ▼
Flask Route Handler
      │
      │  render_template() → HTML response
      ▼
Frontend (rendered page in browser)
```

### Request Lifecycle

| Step | Actor | Action |
|---|---|---|
| 1 | Browser | User submits login form |
| 2 | Flask Router | Matches `/login` POST route |
| 3 | Auth Service | Validates credentials against DB |
| 4 | Session Manager | Creates server-side session on success |
| 5 | Flask Router | Redirects to `/dashboard` |
| 6 | Dashboard Route | Fetches balance from DB |
| 7 | Jinja2 Template | Renders dashboard with account data |
| 8 | Browser | Displays dashboard to user |

---

## 3. Component Design

### Frontend Responsibilities

- Render all user-facing pages using Jinja2 HTML templates served by Flask.
- Apply Bootstrap for layout, responsive grid, form styling, and feedback alerts.
- Collect and submit user input (login credentials, transaction amounts) via HTML forms.
- Display server-side messages (success confirmations, validation errors) using Bootstrap alert components.
- Enforce basic client-side input constraints (required fields, numeric amounts) via HTML5 form attributes.
- Provide navigation between dashboard, deposit, withdraw, and logout via a Bootstrap Navbar.

### Backend Responsibilities

- Expose URL routes for every user action: login, logout, dashboard, deposit, withdraw.
- Authenticate requests by checking session state before serving protected routes.
- Implement all business rules: password verification, deposit validation, withdrawal eligibility check.
- Communicate with the database layer to read account data and persist transactions.
- Manage user sessions using Flask's built-in session mechanism (server-side cookie).
- Return rendered HTML responses or redirects; no JSON API surface at this stage.

### Database Responsibilities

- Persist all application state: user credentials, account balances, and transaction records.
- Serve as the single source of truth for current account balance.
- Provide atomic read-modify-write operations for deposit and withdrawal to prevent inconsistency.
- Store passwords in hashed form only; never plaintext.
- Reside as a single `.db` file within the `BACKEND/` folder for portability.

---

## 4. Folder Structure

```
banking-workshop/
│
├── IMPLEMENTATION_PLAN.md          ← This document
│
├── FRONTEND/                       ← All UI templates and static assets
│   ├── templates/                  ← Jinja2 HTML templates (served by Flask)
│   │   ├── base.html               ← Shared layout: navbar, Bootstrap CDN link
│   │   ├── login.html              ← Login form page
│   │   ├── dashboard.html          ← Account summary / balance view
│   │   ├── deposit.html            ← Deposit funds form
│   │   └── withdraw.html           ← Withdraw funds form
│   └── static/                     ← Optional: custom CSS or images
│       └── css/
│           └── custom.css          ← Minor style overrides (if any)
│
└── BACKEND/                        ← Flask application and database
    ├── app.py                      ← Flask app entry point; registers all routes
    ├── routes/                     ← Route handlers grouped by feature
    │   ├── auth.py                 ← /login, /logout routes
    │   ├── dashboard.py            ← /dashboard route
    │   └── transactions.py         ← /deposit, /withdraw routes
    ├── services/                   ← Business logic, decoupled from HTTP layer
    │   ├── auth_service.py         ← Credential validation, session helpers
    │   └── account_service.py      ← Balance retrieval, deposit, withdrawal logic
    ├── database/                   ← Database initialisation and access helpers
    │   ├── db.py                   ← Connection management, query helpers
    │   └── init_db.py              ← Schema creation and seed data script
    ├── banking.db                  ← SQLite database file (auto-created on init)
    └── config.py                   ← App configuration (secret key, DB path, debug flag)
```

### Folder Responsibilities

| Folder / File | Responsibility |
|---|---|
| `FRONTEND/templates/` | Jinja2 HTML pages rendered and returned by Flask routes |
| `FRONTEND/static/` | Optional static assets (CSS overrides, images) |
| `BACKEND/app.py` | Application factory; registers blueprints and configuration |
| `BACKEND/routes/` | Thin HTTP layer — parse request, call service, return response |
| `BACKEND/services/` | All business rules and data orchestration logic |
| `BACKEND/database/` | Database connection, schema setup, and raw query helpers |
| `BACKEND/config.py` | Environment-specific settings kept separate from application logic |
| `BACKEND/banking.db` | SQLite data file; the sole persistence store |

---

## 5. Module Breakdown

### Authentication Module

**Purpose:** Control access to the application.

| Concern | Detail |
|---|---|
| Entry point | `BACKEND/routes/auth.py` |
| Business logic | `BACKEND/services/auth_service.py` |
| Pages | `login.html` |
| Key behaviours | Verify username/password, create session on success, destroy session on logout |
| Guard mechanism | A `login_required` decorator applied to all protected routes |
| Failure handling | Re-render login page with an error message on bad credentials |

---

### Dashboard Module

**Purpose:** Provide a post-login landing page with account summary.

| Concern | Detail |
|---|---|
| Entry point | `BACKEND/routes/dashboard.py` |
| Business logic | `BACKEND/services/account_service.py` |
| Pages | `dashboard.html` |
| Key behaviours | Retrieve and display current balance; surface quick-action links to deposit/withdraw |
| Access control | Redirect to login if no valid session exists |

---

### Account Management Module

**Purpose:** Own the customer account data and balance state.

| Concern | Detail |
|---|---|
| Business logic | `BACKEND/services/account_service.py` |
| Database access | `BACKEND/database/db.py` |
| Key behaviours | Fetch current balance for a given user; encapsulate all account read operations |
| Shared by | Dashboard, Transactions modules |

---

### Transactions Module

**Purpose:** Process deposit and withdrawal operations.

| Concern | Detail |
|---|---|
| Entry point | `BACKEND/routes/transactions.py` |
| Business logic | `BACKEND/services/account_service.py` |
| Pages | `deposit.html`, `withdraw.html` |
| Key behaviours | Validate amount is positive; check sufficient funds before withdrawal; update balance atomically; confirm success to user |
| Error cases | Negative/zero amount rejected; withdrawal blocked if balance insufficient |
| Feedback | Bootstrap success/danger alert rendered on the next page load |

---

## 6. Implementation Roadmap

### Development Phases

#### Phase 1 — Project Scaffolding *(~0.5 day)*

- Initialise folder structure (`FRONTEND/`, `BACKEND/`).
- Set up Python virtual environment and install Flask.
- Create `app.py` with minimal Flask app; verify it runs.
- Create `config.py` with placeholder values.
- Create `base.html` with Bootstrap CDN and navbar skeleton.

**Dependency:** None — starting point for all subsequent phases.

---

#### Phase 2 — Database Initialisation *(~0.5 day)*

- Implement `database/db.py` (connection helper).
- Implement `database/init_db.py` (schema creation and one seed customer account).
- Verify database file is created correctly on script execution.

**Dependency:** Phase 1 complete.

---

#### Phase 3 — Authentication *(~1 day)*

- Implement `services/auth_service.py` (password hashing + verification).
- Implement `routes/auth.py` (`/login` GET/POST, `/logout`).
- Build `login.html` with Bootstrap form and error alert.
- Implement `login_required` decorator.
- End-to-end test: log in with seed account → session created → redirect to dashboard placeholder.

**Dependency:** Phase 2 complete.

---

#### Phase 4 — Dashboard & Balance View *(~0.5 day)*

- Implement `routes/dashboard.py` (`/dashboard` GET).
- Extend `services/account_service.py` with balance fetch.
- Build `dashboard.html` showing balance card and action buttons.
- Apply `login_required` guard.

**Dependency:** Phase 3 complete.

---

#### Phase 5 — Deposit & Withdrawal *(~1 day)*

- Extend `services/account_service.py` with deposit and withdrawal logic.
- Implement `routes/transactions.py` (`/deposit`, `/withdraw` GET/POST).
- Build `deposit.html` and `withdraw.html` forms with Bootstrap validation feedback.
- Verify balance updates correctly; confirm insufficient-funds guard works.

**Dependency:** Phase 4 complete.

---

#### Phase 6 — Integration & Polish *(~0.5 day)*

- Wire all routes into `app.py` via Flask Blueprints.
- Ensure consistent navigation in `base.html` (show/hide links based on session state).
- Cross-browser smoke test of full user journey: login → view balance → deposit → withdraw → logout.
- Clean up any hardcoded values; move to `config.py`.

**Dependency:** Phases 3–5 complete.

---

### Estimated Effort Summary

| Phase | Effort |
|---|---|
| Phase 1 — Scaffolding | 0.5 day |
| Phase 2 — Database Init | 0.5 day |
| Phase 3 — Authentication | 1.0 day |
| Phase 4 — Dashboard & Balance | 0.5 day |
| Phase 5 — Deposit & Withdrawal | 1.0 day |
| Phase 6 — Integration & Polish | 0.5 day |
| **Total** | **4.0 days** |

---

### Dependency Chain

```
Phase 1 (Scaffold)
      │
      ▼
Phase 2 (Database)
      │
      ▼
Phase 3 (Authentication)
      │
      ▼
Phase 4 (Dashboard)
      │
      ▼
Phase 5 (Transactions)
      │
      ▼
Phase 6 (Integration)
```

> All phases are sequential. Each phase produces a testable, working increment of the application.

---

*End of Implementation Plan*
