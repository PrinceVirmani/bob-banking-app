# Banking Web Application — Step-by-Step Implementation Guide

> **Reference:** [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)  
> **Document Type:** Implementation Instructions (Plain English)  
> **Stack:** HTML + Bootstrap · Python Flask · SQLite  
> **Audience:** Developer building the application from scratch

---

## How to Use This Guide

Work through each section in order. Every section maps directly to a phase in the
Implementation Plan. Instructions are written in plain English — they describe *what to
build* and *how the logic should work*, not the exact code to copy.

---

## 1. Environment Setup

### 1.1 Prerequisites Check

Before writing a single line of code, confirm that the following tools are available on
your machine:

- **Python 3.10 or newer** — run `python3 --version` in your terminal to check.
- **pip** — Python's package manager, usually bundled with Python.
- **A code editor** — VS Code, PyCharm, or any editor you are comfortable with.
- **A web browser** — Chrome or Firefox for testing.

If Python is not installed, download it from python.org and follow the installer. On
macOS, you can also install it via Homebrew.

---

### 1.2 Create the Project Folder Structure

Create the top-level workspace folder and then create the two main sub-folders inside
it: one called `FRONTEND` and one called `BACKEND`. These two folders are the
foundational separation that the entire application is built around.

Inside `FRONTEND`, create two sub-folders: `templates` and `static/css`. The
`templates` folder will hold every HTML page. The `static/css` folder is where any
optional custom stylesheet lives.

Inside `BACKEND`, create three sub-folders: `routes`, `services`, and `database`.
These correspond to the three logical layers of the backend — HTTP handling, business
logic, and data access respectively.

```
banking-workshop/
├── FRONTEND/
│   ├── templates/
│   └── static/css/
└── BACKEND/
    ├── routes/
    ├── services/
    └── database/
```

---

### 1.3 Set Up a Python Virtual Environment

A virtual environment keeps the project's Python packages isolated from the rest of
your machine, preventing version conflicts.

Navigate into the `BACKEND` folder in your terminal. Create a new virtual environment
there by running the Python venv command. This produces a folder (commonly named
`venv`) inside `BACKEND` that contains its own copy of Python and pip.

Activate the virtual environment. On macOS/Linux the activation command sources a
shell script inside the `venv/bin` folder. On Windows it runs a script in
`venv\Scripts`. Once active, your terminal prompt will show the environment name,
confirming that any packages you install will go into this isolated environment.

> **Important:** Always activate the virtual environment before running the app or
> installing packages. If you open a new terminal window, you need to activate it
> again.

---

### 1.4 Install Flask and Dependencies

With the virtual environment active, use pip to install the required packages:

- **Flask** — the web framework.
- **Werkzeug** — ships with Flask and provides the password hashing utilities you will
  use for secure credential storage.

After installation, verify by running `flask --version`. You should see a version
number printed. If you see an error, the virtual environment may not be activated.

Create a `requirements.txt` file in the `BACKEND` folder listing the packages you
installed. This file allows any other developer (or a server) to recreate the same
environment by running `pip install -r requirements.txt`.

---

### 1.5 Create the Flask Entry Point

Create a file called `app.py` at the root of the `BACKEND` folder. This is the file
you will run to start the web server.

Inside `app.py`, do the following in order:

1. Import Flask.
2. Create a Flask application instance, telling it where to find templates. Because
   the templates live in the `FRONTEND/templates` folder (not the default location
   Flask expects), you need to pass the explicit path when creating the app.
3. Set a secret key on the app. This key is used by Flask to cryptographically sign
   session cookies. Use a long, random string for this. For development a hard-coded
   value is fine; in production it must come from an environment variable.
4. Add a block at the bottom that runs the Flask development server only when the
   script is executed directly (not when it is imported as a module).

At this point you should be able to run `python app.py` from inside `BACKEND` and see
Flask start up on `http://127.0.0.1:5000`. Visiting that URL in a browser will return
a 404 (since no routes exist yet), which is expected and correct.

---

### 1.6 Create the Configuration File

Create `config.py` inside `BACKEND`. This file holds application-wide settings as
plain Python variables:

- The path to the SQLite database file.
- The secret key for session signing.
- A debug flag that is `True` during development and `False` in production.

In `app.py`, import and apply these values instead of writing them directly. This
separation means you only ever need to change one file when deploying to a different
environment.

---

## 2. Backend Implementation

### 2.1 Database Layer — `database/db.py`

This file is the single place in the entire application that opens a connection to the
SQLite file. Every other part of the backend asks this module for a connection rather
than opening one directly.

The logic inside `db.py` should:

- Know the path to `banking.db` (read it from `config.py`).
- Provide a function that opens and returns a database connection. Configure the
  connection to return rows as dictionary-like objects so you can access columns by
  name (e.g., `row['balance']`) rather than by index.
- Optionally, provide a function that closes the connection. Flask has a teardown
  mechanism you can hook into so the connection closes automatically at the end of
  each request.

---

### 2.2 Database Initialisation — `database/init_db.py`

This is a one-time setup script, not part of the web app itself. Running it creates
the database tables and inserts at least one test customer so you have something to
log in with during development.

The script should:

1. Open a connection using `db.py`.
2. Create a `users` table that stores a unique username and a hashed password.
3. Create an `accounts` table that links each user to a current balance (a decimal
   number, defaulting to zero).
4. Create a `transactions` table that records every deposit and withdrawal — storing
   the user it belongs to, whether it was a deposit or withdrawal, the amount, and a
   timestamp.
5. Insert one test user. Hash the test password using Werkzeug's hashing function
   before storing it — never write a plaintext password into the database.
6. Insert a corresponding account row for that test user with a starting balance (e.g.,
   1000.00).
7. Commit the changes and close the connection.

Run this script once from the terminal. After it runs, a `banking.db` file should
appear in the `BACKEND` folder.

---

### 2.3 Authentication Service — `services/auth_service.py`

This file contains the business logic for all authentication operations. It knows
nothing about HTTP requests or HTML — it just works with usernames, passwords, and
database rows.

**Login verification logic:** Accept a username and a plaintext password as input.
Query the `users` table for a row matching that username. If no row is found, return a
failure signal. If a row is found, use Werkzeug's `check_password_hash` function to
compare the supplied plaintext password against the stored hash. Return success only
if the hash comparison passes.

**Why hash comparison instead of direct comparison:** Hashing is a one-way operation.
The database never stores the original password, only a scrambled version. An attacker
who steals the database cannot recover the original passwords. Werkzeug handles all the
complexity of the hashing algorithm and the salt.

---

### 2.4 Account Service — `services/account_service.py`

This file contains all logic related to the customer's account balance and
transactions. Like the auth service, it operates purely on data — no HTTP concerns.

**Get balance:** Accept a user ID. Query the `accounts` table for the row belonging to
that user. Return the balance value.

**Deposit logic:** Accept a user ID and an amount. Add the amount to the current
balance in the `accounts` table. Insert a new row into the `transactions` table
recording this deposit. Commit the change. Both the update and the insert should happen
in the same database transaction so they either both succeed or both fail together.

**Withdrawal logic:** Accept a user ID and an amount. First fetch the current balance.
Check whether the balance is greater than or equal to the requested amount. If not,
return a failure signal (do not touch the database). If yes, subtract the amount from
the balance, update the `accounts` table, insert a transaction record, and commit.

---

### 2.5 Route: Authentication — `routes/auth.py`

This file handles the `/login` and `/logout` URLs. Think of routes as the receptionist
— they receive the incoming request, hand off the real work to a service, and decide
what response to send back.

**GET `/login`:** Simply render the `login.html` template. This is what the user sees
when they visit the login page for the first time.

**POST `/login`:** Read the username and password from the submitted form data. Pass
them to the auth service's verification function. If verification fails, render
`login.html` again but pass an error message string to the template so it can display
a Bootstrap danger alert. If verification succeeds, store the logged-in user's ID (and
optionally their username) in Flask's `session` dictionary, then redirect to
`/dashboard`.

**GET `/logout`:** Clear the Flask session dictionary entirely. Redirect to the login
page. The user is now effectively logged out — their session cookie no longer maps to
any stored data.

---

### 2.6 The `login_required` Decorator

A decorator is a Python pattern that wraps a function with additional behaviour. Create
a `login_required` function in a shared helpers file (or inside `auth_service.py`).

The decorator's logic: before the wrapped route function runs, check whether a user ID
exists in the current Flask session. If it does, allow the route to proceed normally.
If it does not, redirect the user to the login page immediately without running the
route's code.

Apply this decorator to every route except `/login` and `/logout`. This ensures that
unauthenticated users can never access the dashboard or perform transactions — even if
they type the URL directly.

---

### 2.7 Route: Dashboard — `routes/dashboard.py`

**GET `/dashboard`:** This route is protected by `login_required`. Read the user ID
from the session. Call the account service to fetch the current balance for that user.
Render `dashboard.html`, passing the balance value and the username to the template.

The route itself does nothing complex — all the interesting work happens in the
service. The route's only job is to bridge the HTTP world (session, request, response)
with the business logic world (services).

---

### 2.8 Route: Transactions — `routes/transactions.py`

Both deposit and withdraw follow the same pattern, so understanding one means
understanding both.

**GET `/deposit`:** Render the `deposit.html` form. Nothing else.

**POST `/deposit`:** Read the amount the user typed from the form data. Convert it from
a string to a number (form data is always a string). Pass the user ID (from session)
and the amount to the account service's deposit function. On success, redirect to
`/dashboard` with a success message passed via Flask's `flash` mechanism. On any
validation error (caught before reaching the service), re-render the form with an
error message.

**GET `/withdraw`** and **POST `/withdraw`:** Identical pattern to deposit. The only
difference is calling the withdrawal function and handling the extra failure case where
the balance is insufficient — in that case, show an error on the withdraw page rather
than redirecting.

---

### 2.9 Session Management

Flask's session works like a dictionary that is attached to the current user's browser
session via a signed cookie. Anything you put into `session[...]` persists across
requests for that same browser session.

Key session operations you will use:

- **Store on login:** After verifying credentials, write `session['user_id']` and
  `session['username']`.
- **Read on protected routes:** The `login_required` decorator checks
  `session.get('user_id')`.
- **Clear on logout:** Call `session.clear()` to remove all stored values.

The Flask secret key is what makes sessions secure — it cryptographically signs the
cookie so the browser cannot tamper with its contents.

---

### 2.10 Error Handling

Apply consistent error handling across all routes:

- **Invalid form input** (non-numeric amount, empty field): Catch this at the route
  level before calling any service. Re-render the same form with an error message.
- **Business logic failures** (insufficient funds, unknown user): The service returns a
  failure signal (e.g., `None`, `False`, or a tuple containing a status). The route
  checks this signal and re-renders with an appropriate message.
- **Unexpected database errors**: Wrap database calls in try/except blocks. If an
  unexpected error occurs, show a generic "Something went wrong" message and log the
  real error to the console. Do not expose raw database error messages to the user.

---

## 3. Frontend Implementation

### 3.1 The Base Template — `base.html`

All pages should share a common outer shell. In Jinja2, this is done with template
inheritance. Create `base.html` as the parent template.

`base.html` should contain:

- The standard HTML document structure (`<!DOCTYPE html>`, `<html>`, `<head>`,
  `<body>`).
- A `<link>` tag in `<head>` pointing to the Bootstrap CDN stylesheet.
- A Bootstrap Navbar at the top of the page. The navbar should show the app name on
  the left. On the right, if the user is logged in (check a template variable passed
  from Flask), show navigation links to Dashboard, Deposit, Withdraw, and Logout. If
  not logged in, show nothing (or just the Login link).
- A main content area in the `<body>` that contains a Jinja2 `block` named `content`.
  Each child page will fill this block with its own HTML.
- A section just above the content area that loops over Flask's `flashed messages` and
  renders each one as a Bootstrap alert. This is how success and error messages will
  appear on every page without duplicating the alert HTML.

---

### 3.2 Login Page — `login.html`

Extend `base.html`. Fill the content block with a centered Bootstrap card.

Inside the card:

- A heading: "Sign In" or "Customer Login".
- An HTML form with `method="POST"` and `action="/login"`.
- A text input field for username with the `name` attribute set to `username`.
- A password input field for password with the `name` attribute set to `password`.
- A "Login" submit button styled as a Bootstrap primary button.

If the route passed an error message to the template, render it as a Bootstrap
`alert-danger` above the form. Use a Jinja2 conditional to only show the alert when an
error exists.

Do not add any client-side JavaScript validation on this form — server-side validation
is sufficient for this application.

---

### 3.3 Dashboard Page — `dashboard.html`

Extend `base.html`. This page is the user's home screen after logging in.

The page should contain:

- A greeting that uses the username passed from Flask (e.g., "Welcome, Alice").
- A Bootstrap card prominently displaying the current balance. Format the balance to
  two decimal places. Show a currency symbol.
- Two Bootstrap buttons below the balance card: one linking to `/deposit` and one
  linking to `/withdraw`. Style them as outlined or solid buttons in contrasting
  colours.
- Any flashed messages from the previous request (handled automatically by `base.html`).

The dashboard is read-only — it shows information and provides navigation, but
contains no forms that modify data.

---

### 3.4 Deposit Page — `deposit.html`

Extend `base.html`. Fill the content block with a Bootstrap card containing a form.

The form should have:

- `method="POST"` and `action="/deposit"`.
- A number input field for the deposit amount. Set the `min` attribute to `0.01` and
  `step` to `0.01` so the browser's native number input handles decimal values
  correctly. Mark the field as `required`.
- A "Deposit" submit button.
- A "Back to Dashboard" link styled as a secondary button.

Display any error messages passed from Flask as Bootstrap alerts above the form.

---

### 3.5 Withdraw Page — `withdraw.html`

This page is structurally identical to the deposit page. The only differences are:

- The form action points to `/withdraw`.
- The heading and button label say "Withdraw" instead of "Deposit".
- The error message section needs to handle the additional case of "insufficient
  funds".

Since the two forms are so similar, consider extracting the amount-input form into a
Jinja2 macro or partial to avoid duplication — though for this scale of project,
duplicating the two templates is also acceptable.

---

### 3.6 Bootstrap Layout Guidelines

Apply these Bootstrap conventions consistently across all pages:

- Wrap page content in a `<div class="container mt-4">` to centre it and add top
  spacing.
- Use `<div class="row justify-content-center">` with a `<div class="col-md-6">` to
  keep forms narrow and centered on wider screens.
- Use `card`, `card-body`, and `card-header` classes for the white box around forms
  and the balance display.
- Use `btn btn-primary` for the main action button, `btn btn-secondary` for
  back/cancel links.
- Use `alert alert-danger` for error messages and `alert alert-success` for
  confirmations.
- Use `form-label` and `form-control` classes on form labels and inputs respectively.
- Keep the Navbar using `navbar navbar-expand-lg navbar-dark bg-dark` for a consistent
  dark header across all pages.

---

## 4. Integration Steps

### 4.1 Tell Flask Where Templates and Static Files Live

Because the templates are in `FRONTEND/templates/` rather than the default
`templates/` folder Flask expects, you need to pass the correct path when creating
the Flask app instance. Calculate the path relative to where `app.py` lives so it
works regardless of which directory you run Flask from.

Similarly, tell Flask where the static files folder is so it can serve the custom
CSS file.

---

### 4.2 Register Blueprints in `app.py`

A Flask Blueprint is a way of organising routes into groups. Each routes file
(`auth.py`, `dashboard.py`, `transactions.py`) should define a Blueprint and register
its routes on that Blueprint instead of directly on the app.

In `app.py`, import each Blueprint object and register it with the Flask app using
`app.register_blueprint(...)`. This is the step that wires all the URL routes into the
running application. After doing this, Flask knows about `/login`, `/logout`,
`/dashboard`, `/deposit`, and `/withdraw`.

---

### 4.3 Connect Flask Routes to Services

Each route file imports the service functions it needs. A route never queries the
database directly — it always goes through a service function. This keeps the HTTP
logic and the business logic completely separate, making each part independently
testable.

The flow for every POST request is the same:

1. Extract form data from the incoming request.
2. Do a basic type and format check (is it a number? is it non-empty?).
3. Call the relevant service function with the cleaned data.
4. Check the return value to determine success or failure.
5. Respond with a redirect (on success) or re-render the form (on failure).

---

### 4.4 Connect the Database Module to Services

Each service file imports the database connection function from `database/db.py`. When
a service needs to read or write data, it calls `get_connection()`, uses the returned
connection to execute SQL queries, and then closes or releases the connection.

Do not use an ORM (like SQLAlchemy) at this stage — plain Python `sqlite3` with
parameterised queries is sufficient and easier to reason about. Always use
parameterised queries (`?` placeholders) rather than string formatting to prevent SQL
injection.

---

### 4.5 Flash Messages — The Bridge Between Redirects and Pages

When a POST request succeeds, Flask best practice is to redirect to a GET page (the
Post/Redirect/Get pattern). But you need to show the user a "Deposit successful"
message on that page. This is what Flask's `flash()` function is for.

Before redirecting, call `flash("Your deposit was successful.", "success")`. The
second argument is the category — use `"success"` or `"danger"` to match Bootstrap
alert colour classes. The `base.html` template should already be looping over flashed
messages and rendering them as alerts. Nothing extra is needed in the destination
route.

---

## 5. Validation Rules

### 5.1 Login Validation

Apply these checks in the login route, before calling the auth service:

| Check | Rule | Response on Failure |
|---|---|---|
| Username present | The username field must not be empty or whitespace-only | Re-render login with "Please enter your username" |
| Password present | The password field must not be empty | Re-render login with "Please enter your password" |
| Credentials valid | Auth service must confirm username+password match | Re-render login with "Invalid username or password" |

**Important:** Always return the same generic message for invalid credentials
regardless of whether the username or the password was wrong. Revealing which one
failed is an information leak that helps attackers.

---

### 5.2 Balance Validation

The account service should enforce these rules when reading balance data:

| Check | Rule |
|---|---|
| User exists | The user ID from the session must map to an existing account row |
| Balance is numeric | The value returned from SQLite must be a number before arithmetic is performed |

If a user ID from the session does not match any account, something has gone
structurally wrong (data inconsistency). In this case, clear the session and redirect
to login — do not let the user proceed.

---

### 5.3 Deposit Validation

Apply these checks in the deposit route, before calling the account service:

| Check | Rule | Response on Failure |
|---|---|---|
| Amount present | The amount field must not be empty | Re-render form with "Please enter an amount" |
| Amount is numeric | Must be convertible to a float without error | Re-render form with "Amount must be a number" |
| Amount is positive | Must be greater than zero | Re-render form with "Amount must be greater than zero" |
| Amount is reasonable | Optionally, enforce a maximum single-deposit limit | Re-render form with the limit message |

---

### 5.4 Withdrawal Validation

Apply all the same checks as deposit, plus one additional check:

| Check | Rule | Response on Failure |
|---|---|---|
| Amount present | The amount field must not be empty | Re-render form with "Please enter an amount" |
| Amount is numeric | Must be convertible to a float | Re-render form with "Amount must be a number" |
| Amount is positive | Must be greater than zero | Re-render form with "Amount must be greater than zero" |
| Sufficient funds | Current balance must be ≥ requested amount | Re-render form with "Insufficient funds" |

The insufficient-funds check must happen inside the account service, not only in the
route. The service owns the business rule; the route just communicates the outcome to
the user.

---

## 6. Testing

### 6.1 Unit Tests

Unit tests check individual functions in isolation, without starting the Flask server
or touching the real database.

**What to unit test:**

- **Auth service:** Test that `verify_credentials` returns success when given a
  username with a correctly hashed password. Test that it returns failure when the
  password is wrong. Test that it returns failure when the username does not exist.
  Use a temporary in-memory SQLite database (not the real `banking.db`) so tests are
  fast and isolated.

- **Account service — deposit:** Test that calling deposit increases the balance by
  the correct amount. Test that a deposit of zero is rejected. Test that a negative
  deposit is rejected.

- **Account service — withdrawal:** Test that a valid withdrawal decreases the balance
  correctly. Test that a withdrawal exceeding the balance is rejected and the balance
  is unchanged.

Organise unit tests in a `tests/` folder inside `BACKEND`. Use Python's built-in
`unittest` module or the `pytest` framework (install via pip). Name test files with a
`test_` prefix so the test runner finds them automatically.

---

### 6.2 Integration Tests

Integration tests check that multiple components work together correctly — routes,
services, and the database all running together through Flask's test client.

**What to integrate-test:**

- **Login flow:** POST to `/login` with valid credentials → assert redirect to
  `/dashboard`. POST with invalid credentials → assert response contains the error
  message.

- **Dashboard access:** GET `/dashboard` without a session → assert redirect to
  `/login`. GET `/dashboard` with a valid session → assert the balance appears in the
  response.

- **Deposit flow:** POST to `/deposit` with a valid amount while logged in → assert
  redirect to dashboard and that balance has increased.

- **Withdrawal flow:** POST to `/withdraw` with an amount exceeding the balance →
  assert the form is re-rendered with an error message and the balance is unchanged.

Use Flask's built-in `test_client()` to send requests without starting a real server.
Use a fresh temporary database for each test run to avoid state leaking between tests.

---

### 6.3 Manual Testing Checklist

After automated tests pass, walk through this checklist in a real browser to catch
anything automated tests might miss:

**Authentication**
- [ ] Visiting `/dashboard` without logging in redirects to `/login`
- [ ] Logging in with wrong password shows an error message
- [ ] Logging in with correct credentials redirects to the dashboard
- [ ] Logging out clears the session and redirects to login
- [ ] After logout, pressing the browser back button does not re-enter the dashboard

**Dashboard**
- [ ] Dashboard shows the correct starting balance
- [ ] Customer name is displayed correctly
- [ ] Deposit and Withdraw buttons navigate to the correct pages

**Deposit**
- [ ] Submitting a blank amount shows a validation error
- [ ] Submitting a negative amount shows a validation error
- [ ] Submitting a valid amount redirects to dashboard with a success message
- [ ] The balance on the dashboard has increased by exactly the deposited amount

**Withdrawal**
- [ ] Submitting a blank amount shows a validation error
- [ ] Submitting an amount greater than the balance shows "Insufficient funds"
- [ ] Submitting a valid amount redirects to dashboard with a success message
- [ ] The balance on the dashboard has decreased by exactly the withdrawn amount

**UI / Responsiveness**
- [ ] All pages render without broken layout at desktop width (1280px)
- [ ] All pages render without broken layout at tablet width (768px)
- [ ] Bootstrap alerts are visible and correctly coloured (green/red)
- [ ] The navbar collapses to a hamburger menu on mobile width

---

## 7. Deployment

### 7.1 Run Locally (Development)

Running locally uses Flask's built-in development server. This is the correct way to
run the app during development.

Steps:

1. Open a terminal and navigate to the `BACKEND` folder.
2. Activate the virtual environment.
3. If you have not already done so, run `init_db.py` to create the database and seed
   data.
4. Run `python app.py`. Flask will print the local URL (typically
   `http://127.0.0.1:5000`).
5. Open that URL in a browser.

To stop the server, press `Ctrl+C` in the terminal.

> **Development server warning:** Flask's built-in server is single-threaded and not
> hardened for security. It is suitable for local development only. Never use it to
> serve real users.

---

### 7.2 Environment Variables

Before deploying anywhere beyond your local machine, remove any hard-coded sensitive
values from `config.py`. The following should come from environment variables:

- `SECRET_KEY` — the string Flask uses to sign session cookies. Generate a
  cryptographically random value (at least 32 characters). If this is leaked or
  guessable, session cookies can be forged.
- `DATABASE_PATH` — optional, but useful if the deployment directory structure differs
  from development.
- `DEBUG` — must be `False` in any non-development environment.

Set environment variables on the deployment machine or via a `.env` file loaded at
startup. Never commit a `.env` file to version control.

---

### 7.3 Production Considerations

When moving beyond local use, address the following before exposing the application to
real users:

| Concern | Action Required |
|---|---|
| WSGI Server | Replace Flask's built-in server with a production WSGI server such as **Gunicorn** (Linux/macOS) or **Waitress** (Windows). Install it via pip and point it at the Flask app object. |
| HTTPS | Serve the app behind a reverse proxy (Nginx or Apache) that handles TLS termination. Never send login credentials over plain HTTP. |
| Secret Key | Load from environment variable; use a cryptographically random 32+ character string. |
| Debug Mode | Set `DEBUG = False`. Debug mode exposes an interactive error console in the browser — a critical security hole. |
| Database | SQLite is suitable for single-user or low-concurrency use. For multi-user production traffic, migrate to PostgreSQL or MySQL. |
| Session Timeout | Configure a `PERMANENT_SESSION_LIFETIME` value in Flask so sessions expire after a reasonable idle period (e.g., 30 minutes). |
| Static Files | For production, configure the reverse proxy (Nginx) to serve files from `FRONTEND/static/` directly, bypassing Flask for better performance. |

---

### 7.4 Minimal Deployment Checklist

Before calling the app "deployed", confirm:

- [ ] `DEBUG = False` is set in the configuration
- [ ] `SECRET_KEY` is a long random value loaded from an environment variable
- [ ] The database file is stored outside the web-accessible directory
- [ ] The app is running behind a WSGI server (not Flask's dev server)
- [ ] HTTPS is enabled
- [ ] The test user seed account password has been changed or the seed account removed
- [ ] `requirements.txt` is up to date so the environment can be reproduced

---

*End of Step-by-Step Implementation Guide*
