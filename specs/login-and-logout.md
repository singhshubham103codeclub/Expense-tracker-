# Feature Specification: User Authentication (Login and Logout)

## 1. Feature Title and Summary

- **Feature Name:** User Authentication: Sign In (Login) & Sign Out (Logout)
- **Target Specification File:** `specs/login-and-logout.md`
- **Summary:** Complete user authentication lifecycle for Spendly, allowing registered users to sign in with their email and password, establish an encrypted HTTP session cookie, access authenticated areas of the application, and terminate active sessions via logout. Introduces the `load_logged_in_user` request hook (`g.user`) and a reusable `@login_required` decorator to protect private application views.

---

## 2. Problem Statement

Currently in Spendly:
1. `@templates/login.html` provides a sign-in form targeting `POST /login`, but the route `@app.route("/login")` in `@app.py` only accepts `GET` requests and lacks `POST` submission handling, credential validation, password verification, and session creation. Submitting the form results in an HTTP 405 Method Not Allowed error.
2. The logout route `@app.route("/logout")` in `@app.py` is a placeholder returning the plain string `"Logout — coming in Step 3"`.
3. The navigation bar in `@templates/base.html` statically displays "Sign in" and "Get started" buttons regardless of whether a user is logged in or out.
4. There is no session state management, user loader hook (`g.user`), or route access guard (`@login_required`) to secure private user areas like `@app.route("/profile")` and future expense-tracking routes (`@app.route("/expenses/add")`, etc.).

---

## 3. Goals and Expected Outcomes

- Transform `@templates/login.html` into a fully functioning, accessible login interface.
- Securely verify user passwords against the stored `password_hash` in SQLite using `werkzeug.security.check_password_hash`.
- Manage user sessions safely using Flask's `session` object (`session["user_id"]`), protecting against session fixation by resetting the session upon authentication.
- Implement `@app.route("/logout")` to invalidate user sessions, flash a confirmation notification, and redirect users safely to the landing page.
- Implement a global `before_request` hook (`load_logged_in_user`) that populates `g.user` with the active user record.
- Create a reusable `@login_required` decorator to protect authenticated routes across the application.
- Dynamically update the navigation bar in `@templates/base.html` to reflect authentication state:
  - When authenticated: show the user's name/profile link and a "Sign out" link.
  - When unauthenticated: show "Sign in" and "Get started".
- Retain the entered email address in `@templates/login.html` when authentication fails, while clearing the password field.
- Prevent user enumeration by displaying a uniform error message ("Invalid email or password.") for both non-existent accounts and incorrect passwords.
- Redirect already-authenticated users if they navigate to `/login` or `/register`.

---

## 4. Target Users and User Stories

- **Target User:** Returning Spendly users who need to sign in to access their private budgets and expenses, and active users who want to safely sign out on personal or shared devices.
- **User Stories:**
  - *As a registered user*, I want to sign in with my email and password so that I can access my private expense records and manage my finances.
  - *As a returning user*, I want clear feedback if my email or password was entered incorrectly so that I can re-attempt authentication.
  - *As a security-conscious user*, I want the system not to disclose whether an email address is registered on the platform when a login fails.
  - *As a user on a shared computer*, I want to sign out easily from any page so that subsequent users cannot view my financial records.
  - *As an authenticated user*, I want the navigation bar to acknowledge my signed-in state and provide direct access to sign out.
  - *As a signed-in user*, if I inadvertently visit `/login` or `/register`, I want to be redirected automatically so I don't sign in redundantly.

---

## 5. Functional Requirements

### 5.1 Sign In Page Display (`GET /login`)
- **Route:** `@app.route("/login", methods=["GET", "POST"])`
- **Session Check:** If `g.user` is already authenticated (session contains valid `user_id`), redirect immediately to `url_for("profile")` or `url_for("landing")`.
- **Template Rendering:** Render `@templates/login.html` within `@templates/base.html`.
- **Form Controls:**
  - `email`: Email input (`type="email"`, required, autofocus, `value="{{ email }}"` to preserve input on failure).
  - `password`: Password input (`type="password"`, required).
  - Submit button: "Sign in".
  - Link to `/register`: "Create one free".
- **Notifications:** Render flashed messages (`get_flashed_messages(with_categories=true)`) and inline `error` messages.

### 5.2 Sign In Form Submission (`POST /login`)
- **Input Sanitization:**
  - `email = request.form.get("email", "").strip().lower()`
  - `password = request.form.get("password", "")`
- **Input Validation:**
  - If either `email` or `password` is missing/empty, return HTTP 200 (re-render `@templates/login.html`) with error: `"Please provide both email and password."`, preserving `email`.
- **Credential Verification:**
  - Query SQLite: `SELECT * FROM users WHERE email = ?` with normalized `email`.
  - Check credentials:
    - If user does not exist OR `check_password_hash(user["password_hash"], password)` returns `False`:
      - Return HTTP 200 re-rendering `@templates/login.html` with error: `"Invalid email or password."`.
      - Preserve `email=email` in template context; omit password.
- **Session Establishment (Success):**
  - Call `session.clear()` to prevent session fixation.
  - Set `session["user_id"] = user["id"]`.
  - Set `session["user_name"] = user["name"]`.
  - Flash success notification: `"Welcome back, {user['name']}!"` (`category="success"`).
  - Check for optional `next` parameter in `request.args` (e.g., redirected from a protected route):
    - Validate that `next` is a relative path starting with `/` (prevent open redirect vulnerabilities).
    - If valid, redirect to `next`.
    - Otherwise, redirect to `url_for("landing")` (or `url_for("profile")` once implemented).

### 5.3 Sign Out (`GET /logout` or `POST /logout`)
- **Route:** `@app.route("/logout")`
- **Action:**
  - Call `session.clear()`.
  - Flash confirmation notification: `"You have been signed out."` (`category="success"`).
  - Redirect to `url_for("landing")`.

### 5.4 Global User Session Loader (`before_request`)
- **Hook:** `@app.before_request def load_logged_in_user():`
- **Logic:**
  - Retrieve `user_id = session.get("user_id")`.
  - If `user_id is None`:
    - Set `g.user = None`.
  - If `user_id is not None`:
    - Query database: `get_db().execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()`.
    - If user record exists: `g.user = user`.
    - If user record no longer exists in DB (e.g. database reset):
      - Call `session.clear()`.
      - Set `g.user = None`.

### 5.5 Route Access Control Decorator (`@login_required`)
- **Definition:**
  ```python
  def login_required(view):
      @functools.wraps(view)
      def wrapped_view(**kwargs):
          if g.user is None:
              flash("Please sign in to access this page.", "error")
              return redirect(url_for("login", next=request.path))
          return view(**kwargs)
      return wrapped_view
  ```
- Protects authenticated routes (such as `@app.route("/profile")` and future expense CRUD routes).

### 5.6 Navigation Bar Conditional Rendering (`@templates/base.html`)
- Update `@templates/base.html` navigation links container (`.nav-links`):
  - **When user is authenticated (`g.user` is truthy):**
    - Display link to profile / user name: `<a href="{{ url_for('profile') }}">Profile</a>` (or user greeting).
    - Display Sign out link: `<a href="{{ url_for('logout') }}" class="nav-cta">Sign out</a>`.
  - **When user is unauthenticated (`g.user` is falsy):**
    - Display `<a href="{{ url_for('login') }}">Sign in</a>`.
    - Display `<a href="{{ url_for('register') }}" class="nav-cta">Get started</a>`.

---

## 6. Non-Functional Requirements

- **Security:**
  - **Password Security:** Use `werkzeug.security.check_password_hash` to compare incoming passwords against stored hashes.
  - **User Enumeration Protection:** Return an identical, generic error message (`"Invalid email or password."`) whether the email does not exist or the password does not match.
  - **Session Fixation Defense:** Clear the session (`session.clear()`) prior to assigning `session["user_id"]`.
  - **Open Redirect Defense:** Validate any `next` query parameter using standard relative URL checks (`url_parse` / `request.args.get("next")` starting with `/` and not `//`).
  - **Case-Insensitive Authentication:** Normalize email addresses with `.strip().lower()` to ensure reliable authentication regardless of input casing.
  - **SQL Injection Prevention:** Use parameterized queries (`?` placeholders) for all SQLite interactions.
- **Accessibility:**
  - Error messages in `@templates/login.html` rendered with `role="alert"` for assistive technologies.
  - Maintain existing form label associations (`for="email"` and `for="password"` matching `id` attributes).
  - All interactive navigation links must be keyboard focusable with visible focus rings.
- **Performance:**
  - Lookup by email leverages the existing unique index `idx_users_email` in SQLite.
  - Single fast query execution per authentication request (< 5ms database query time).

---

## 7. UI/UX Behavior and Design System Alignment

- **Aesthetic Consistency:**
  - Adhere to Spendly's warm paper editorial design system (`--paper: #fbf9f5`, `--paper-card: #ffffff`, `--ink: #1f2421`, `--accent: #1a472a`).
  - Maintain typography: headings in `DM Serif Display`, UI and forms in `DM Sans`.
  - Use `.auth-error` (`--danger-light` background, `--danger` text) and `.auth-success` (`--accent-light` background, `--accent` text) matching existing styles in `@static/css/style.css`.
- **Form Retention:**
  - When authentication fails, the email input must retain the entered email value (`value="{{ email }}"`).
  - The password input must always be cleared for security.
  - The email input maintains `autofocus` on initial load.
- **Navigation Bar Integration:**
  - Ensure `.nav-links` styling gracefully accommodates "Profile" and "Sign out" without layout shifts.
  - Maintain responsive breakpoints at `768px` and `480px` as defined in `@static/css/style.css`.

---

## 8. Backend, Routes, and API Requirements

### 8.1 Imports and Decorators in `@app.py`
```python
import functools
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
```

### 8.2 Route Implementation Details in `@app.py`

#### User Context Hook
```python
@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if g.user is None:
            session.clear()
```

#### Login Required Decorator
```python
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please sign in to access this page.", "error")
            return redirect(url_for("login", next=request.path))
        return view(**kwargs)
    return wrapped_view
```

#### Sign In Route
```python
@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template(
                "login.html",
                error="Please provide both email and password.",
                email=email,
            )

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template(
                "login.html",
                error="Invalid email or password.",
                email=email,
            )

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        flash(f"Welcome back, {user['name']}!", "success")

        next_url = request.args.get("next")
        if next_url and next_url.startswith("/") and not next_url.startswith("//"):
            return redirect(next_url)

        return redirect(url_for("landing"))

    return render_template("login.html")
```

#### Sign Out Route
```python
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("landing"))
```

#### Protecting Existing Placeholder Routes
```python
@app.route("/profile")
@login_required
def profile():
    return "Profile page — coming in Step 4"
```

---

## 9. Database and Data-Model Changes

- **Schema Modifications:** No schema modifications or database migrations are required.
- **Existing Schema Reused from `@database/db.py`:**
  - The `users` table already contains:
    - `id INTEGER PRIMARY KEY AUTOINCREMENT`
    - `name TEXT NOT NULL`
    - `email TEXT NOT NULL UNIQUE`
    - `password_hash TEXT NOT NULL`
    - `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
  - The index `idx_users_email` is already present for optimal email lookups.
- **Queries Required:**
  - Login authentication: `SELECT * FROM users WHERE email = ?`
  - Active session check: `SELECT id, name, email FROM users WHERE id = ?`

---

## 10. Validation, Authorization, and Security Rules

| Input / Condition | Validation Rule | Result on Violation |
| :--- | :--- | :--- |
| `email` missing | `not email` | Error message: `"Please provide both email and password."`, HTTP 200 |
| `password` missing | `not password` | Error message: `"Please provide both email and password."`, HTTP 200 |
| Unknown `email` | `user is None` | Error message: `"Invalid email or password."`, HTTP 200, retain `email` |
| Incorrect `password` | `check_password_hash == False` | Error message: `"Invalid email or password."`, HTTP 200, retain `email` |
| Already logged in | `g.user is not None` on `GET /login` | Immediate redirect to `url_for("landing")` |
| Unauthenticated access | `g.user is None` on `@login_required` route | Flash `"Please sign in to access this page."`, redirect to `url_for("login", next=request.path)` |
| `next` URL validation | `next_url.startswith("/") and not next_url.startswith("//")` | Fall back to default redirect `url_for("landing")` |

---

## 11. Error States and Edge Cases

- **Non-Existent Email:** Submitting an email that does not exist in the database returns generic `"Invalid email or password."` without disclosing user non-existence.
- **Incorrect Password:** Submitting an existing email with an incorrect password returns the exact same `"Invalid email or password."` message.
- **Mixed-Case Email Input:** User enters `JANE@Example.com`; because email is normalized via `.strip().lower()`, lookup finds `jane@example.com` and authentication succeeds.
- **Deleted User with Active Session Cookie:** If a user account is removed from the database while their session cookie is still valid, `load_logged_in_user` detects `user is None`, calls `session.clear()`, sets `g.user = None`, and prompts sign in on protected routes.
- **Malformed or External `next` Parameter:** Query parameters such as `?next=https://malicious.com` or `?next=//malicious.com` are ignored and safely fall back to `url_for("landing")`.
- **Double Login / Re-registration:** An already-authenticated user navigating directly to `/login` or `/register` is redirected to `landing` to prevent confusing authentication states.

---

## 12. Acceptance Criteria

1. **GET `/login` Rendering:**
   - Navigating to `/login` as an unauthenticated visitor renders `@templates/login.html` with status 200.
   - The form includes an email field, password field, and "Sign in" button.
2. **Missing Input Validation:**
   - Submitting the login form with empty email or empty password renders `"Please provide both email and password."` and retains any provided email.
3. **Invalid Credentials Rejection:**
   - Submitting an unregistered email address displays `"Invalid email or password."` and retains the email in the input field.
   - Submitting a registered email with an invalid password displays `"Invalid email or password."` and clears the password field while retaining the email.
4. **Successful Sign In:**
   - Submitting valid credentials sets `session["user_id"]` and `session["user_name"]`.
   - Flashes `"Welcome back, <Name>!"`.
   - Redirects to `landing` (or destination specified in valid `next` parameter).
5. **Sign Out:**
   - Visiting `/logout` clears the session, flashes `"You have been signed out."`, and redirects to `landing`.
   - Subsequent requests to protected routes require re-authenticating.
6. **Session Context & Navbar State:**
   - When signed in, `@templates/base.html` displays "Profile" and "Sign out" instead of "Sign in" and "Get started".
   - When signed out, `@templates/base.html` displays "Sign in" and "Get started".
7. **Route Protection (`@login_required`):**
   - Accessing `@app.route("/profile")` while unauthenticated redirects to `/login` with an informative error message.
   - Accessing `@app.route("/profile")` while authenticated executes the view successfully.
8. **Already Authenticated Redirection:**
   - Accessing `/login` while authenticated redirects directly to `landing`.

---

## 13. Testing and Verification Plan

### 13.1 Automated Tests in `@tests/test_auth.py`
Extend the existing pytest test suite in `@tests/test_auth.py` with the following test cases:

- `test_login_get_renders_form(client)`: Asserts `GET /login` returns 200 with email, password, and sign-in button.
- `test_login_empty_fields(client)`: Asserts submitting empty fields returns `"Please provide both email and password."`.
- `test_login_nonexistent_user(client)`: Asserts submitting an unknown email returns `"Invalid email or password."` and retains email.
- `test_login_wrong_password(client)`: Registers a test user, attempts login with incorrect password, asserts `"Invalid email or password."` is returned.
- `test_login_success(client)`: Registers a test user, submits correct credentials, asserts redirect to landing, success flash message, and active session `user_id`.
- `test_login_case_insensitive_email(client)`: Registers `user@example.com`, submits login with `USER@EXAMPLE.COM`, asserts successful authentication.
- `test_login_redirect_when_already_authenticated(client)`: Logs in, visits `GET /login`, asserts redirect to landing.
- `test_logout(client)`: Signs in, calls `GET /logout`, asserts redirect, flash message, and session cleared.
- `test_login_required_unauthenticated(client)`: Accesses protected `/profile` without session, asserts redirect to `/login?next=%2Fprofile`.
- `test_login_required_authenticated(client)`: Signs in, accesses protected `/profile`, asserts status 200 and access granted.
- `test_navbar_links_authenticated_vs_unauthenticated(client)`: Verifies navbar renders "Sign in" / "Get started" when logged out, and "Sign out" when logged in.

### 13.2 Manual Verification
- Execute `./venv/bin/pytest tests/test_auth.py` and confirm all tests pass.
- Start local development server via `python app.py` on port 5001.
- In a web browser:
  1. Visit `/login` and submit invalid credentials; verify error message and email value retention.
  2. Sign in with valid user credentials; verify welcome message and updated navbar ("Sign out").
  3. Attempt to visit `/login` while logged in; verify redirection.
  4. Click "Sign out"; verify sign-out flash banner and navbar reset to "Sign in".
  5. Attempt to visit `/profile` directly; verify redirect to `/login` with error prompt.

---

## 14. Implementation Plan Broken into Small, Ordered Tasks

1. **Task 1: Template Enhancements (`@templates/login.html` & `@templates/base.html`)**
   - Update `@templates/login.html` to add `value="{{ email }}"` and `role="alert"` on the error container.
   - Update `@templates/base.html` navigation links to conditionally render Profile/Sign out when `g.user` is present, or Sign in/Get started when absent.
2. **Task 2: User Session Loader & Route Decorator (`@app.py`)**
   - Import `functools`, `session`, `g`, `check_password_hash`.
   - Implement `@app.before_request def load_logged_in_user()`.
   - Implement `@login_required` decorator function.
   - Decorate placeholder `@app.route("/profile")` with `@login_required`.
3. **Task 3: Sign In Route Logic (`@app.py`)**
   - Update `@app.route("/login", methods=["GET", "POST"])` to process form submissions.
   - Add input validation, database lookup, password verification, and session setup.
   - Add redirect to `landing` (or valid `next` param) and redirect if `g.user` is already authenticated.
4. **Task 4: Sign Out Route Logic (`@app.py`)**
   - Update `@app.route("/logout")` to clear the session, flash a sign-out message, and redirect to `landing`.
5. **Task 5: Test Suite & Verification (`@tests/test_auth.py`)**
   - Add automated test cases covering login, invalid credentials, case-insensitivity, logout, session loading, and `@login_required`.
   - Run `./venv/bin/pytest` to verify all tests pass.

---

## 15. Relevant Existing Files and Proposed File Changes

- **Files to Modify:**
  - `@app.py`:
    - Add imports: `functools`, `session`, `g`, `check_password_hash`.
    - Implement `load_logged_in_user` hook.
    - Implement `login_required` decorator.
    - Implement `POST` logic for `/login`.
    - Implement session clearing and redirect for `/logout`.
    - Apply `@login_required` to `/profile`.
  - `@templates/login.html`:
    - Add `value="{{ email }}"` to retain email input on validation failure.
    - Add `role="alert"` attribute to error notification container.
  - `@templates/base.html`:
    - Add Jinja `{% if g.user %}` conditional inside `.nav-links` to toggle between authenticated links (Profile, Sign out) and guest links (Sign in, Get started).
  - `@tests/test_auth.py`:
    - Add tests for sign in, credential validation, session creation, logout, and access control.
- **Files Created:**
  - `specs/login-and-logout.md`: This feature specification document.

---

## 16. Dependencies, Risks, Assumptions, and Open Questions

- **Dependencies:**
  - `werkzeug.security.check_password_hash` (already available in virtual environment).
  - `users` SQLite table and `idx_users_email` index in `@database/db.py` (already created and verified).
- **Assumptions:**
  - Login redirects to `landing` (`/`) until the dashboard or expense list view is implemented in subsequent project steps.
  - A simple session cookie mechanism using Flask's secure signed cookies (`app.secret_key`) satisfies project requirements without requiring third-party authentication extensions (such as Flask-Login).
  - Both `GET /logout` and `POST /logout` can be supported, but a simple `GET /logout` matches the current placeholder route and anchor tag in the navbar.
- **Open Questions & Design Decisions:**
  - *Post-login destination:* Should successful login redirect to `landing` (`/`) or directly to `/profile` until an expense dashboard route (`/expenses`) is built? *(Recommendation: Redirect to `landing` with the personalized greeting banner, or `next` if user was redirected from a protected route).*
  - *Logout method:* While `POST /logout` is standard for CSRF defense in public production web applications, Spendly's current placeholder route is a link (`GET`). Should `GET /logout` be used for simplicity, or should it be a form button? *(Recommendation: Use `GET /logout` to maintain consistency with the existing `@app.route("/logout")` placeholder and nav link styling, with optional support for `POST` if CSRF protection is introduced later).*
