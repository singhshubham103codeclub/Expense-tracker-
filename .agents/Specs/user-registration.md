# Feature Specification: User Registration

## 1. Feature Title and Summary

- **Feature Name:** User Registration & Account Creation
- **Target Specification File:** `specs/user-registration.md`
- **Summary:** Complete user registration workflow for Spendly, allowing new users to create a secure personal account with their full name, email address, and password, persisting user credentials with one-way password hashing in SQLite and redirecting to login or dashboard.

---

## 2. Problem Statement

Spendly currently provides a static registration page template (`@templates/register.html`) with an HTML form, but the registration route (`@app.py`) only responds to `GET` requests and lacks `POST` submission processing. There is no user table in the database (`@database/db.py`), no validation logic, and no password hashing implemented. Submitting the form results in an HTTP 405 Method Not Allowed error. Without backend registration handling, users cannot create accounts to store their personal expenses.

---

## 3. Goals and Expected Outcomes

- Turn the existing registration template into a fully functional registration workflow.
- Securely hash passwords before persistence using `werkzeug.security.generate_password_hash`.
- Enforce strict input validation on full name, email format, and password length.
- Prevent duplicate accounts with case-insensitive unique email enforcement.
- Maintain existing visual aesthetic (DM Serif Display headings, DM Sans body, warm paper palette, green accents).
- Preserve user form input (except password) on validation failure with clear inline/alert error messages.
- Prepare the foundation for session-based user authentication across Spendly.

---

## 4. Target Users and User Stories

- **Target User:** Anyone wanting to start tracking personal expenses on Spendly.
- **User Stories:**
  - *As a new visitor*, I want to register for a Spendly account using my name, email, and password so that I can securely log and manage my private financial data.
  - *As a new user*, I want clear feedback if an email is already registered or if my password is too short so that I can correct it easily.
  - *As a user*, I want my password stored securely so my credentials are protected against data exposure.

---

## 5. Functional Requirements

### 5.1 Registration Page Display (`GET /register`)
- Render `@templates/register.html` within the `@templates/base.html` layout shell.
- Form inputs present:
  - `name`: Full Name (`type="text"`, autofocus, placeholder: "Nitish Kumar", required).
  - `email`: Email Address (`type="email"`, placeholder: "nitish@example.com", required).
  - `password`: Password (`type="password"`, placeholder: "Min. 8 characters", required).
  - Submit button: "Create account".
  - Link to `/login`: "Already have an account? Sign in".

### 5.2 Registration Form Submission (`POST /register`)
- Accept incoming `POST` form data: `name`, `email`, `password`.
- Perform server-side validation:
  1. **Full Name:** Required, trimmed of leading/trailing whitespace, minimum 2 characters, maximum 100 characters.
  2. **Email Address:** Required, trimmed, converted to lowercase, valid email format (RFC standard or regex pattern), maximum 255 characters.
  3. **Password:** Required, minimum 8 characters, maximum 128 characters.
  4. **Uniqueness Check:** Query SQLite `users` table for existing record with normalized email.
- If validation fails:
  - Return HTTP 400 Bad Request (or re-render HTTP 200 with error).
  - Pass `error` message and repopulate previously entered `name` and `email` (leave `password` blank).
- If validation succeeds:
  - Hash password using `generate_password_hash(password, method='scrypt')` (or Werkzeug default).
  - Insert new record into `users` table (`name`, `email`, `password_hash`, `created_at`).
  - Redirect user to `/login` with a flash message: "Account created successfully! Please sign in." (Or directly log user into session and redirect to `/expenses`).

---

## 6. Non-Functional Requirements

- **Security:**
  - Never store plaintext passwords. Use Werkzeug's secure hashing (`generate_password_hash`).
  - Protect against SQL injection via parameterized SQLite queries (`?` placeholders).
  - Normalize emails to lowercase (`email.strip().lower()`) to prevent duplicate accounts differing only by case (e.g., `User@example.com` vs `user@example.com`).
  - Timing attack resilience for email lookup during registration.
- **Accessibility:**
  - All form inputs must have associated `<label>` tags with matching `for` and `id` attributes (already present in template).
  - Error messages must use semantic container with `role="alert"` or `aria-live="polite"`.
- **Usability & UX:**
  - Preserved input fields on error so users don't have to retype name and email.
  - Clean error banner using `.auth-error` class already defined in `@static/css/style.css`.
  - Fast response time (< 50ms database insertion).

---

## 7. UI/UX Behavior and Design System Alignment

- **Design System Consistency:**
  - Container: `.auth-container` with `--auth-width: 440px`.
  - Header: `.auth-title` in `DM Serif Display` with `.auth-subtitle` in `DM Sans`.
  - Form Card: `.auth-card` with white background (`--paper-card`), border (`--border`), and rounded corners (`--radius-md`).
  - Input Fields: `.form-input` with transition on focus to `--accent` (`#1a472a`).
  - Submit Button: `.btn-submit` with `--ink` background and `--accent` hover state.
  - Error Notification: `.auth-error` with `--danger-light` background and `--danger` text.
- **Template Updates Needed in `@templates/register.html`:**
  - Add `value="{{ name }}"` and `value="{{ email }}"` to input elements to retain user input when validation errors occur.
  - Add `minlength="8"` attribute to the password input for client-side feedback matching the placeholder.

---

## 8. Backend, Routes, and API Requirements

### 8.1 Route Definition in `@app.py`
```python
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Validation logic...
        # Database check and insertion...
        # Redirect to login or session setup...
    return render_template("register.html")
```

### 8.2 Flask Secret Key & Session Management
- Ensure `app.secret_key` is configured in `@app.py` so flash messages and sessions work properly.

---

## 9. Database and Data-Model Changes

### 9.1 Schema Definition in `@database/db.py`
```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (email);
```

### 9.2 Database Utility Functions Needed in `@database/db.py`
- `get_db()`: Establishes SQLite connection with `sqlite3.Row` row factory and foreign keys enabled.
- `init_db()`: Executes schema creation scripts to ensure the `users` table exists.

---

## 10. Validation, Authorization, and Security Rules

| Field | Rules | Error Message |
| :--- | :--- | :--- |
| `name` | Non-empty, min 2 chars, max 100 chars | "Please provide your full name." |
| `email` | Non-empty, valid format, max 255 chars | "Please provide a valid email address." |
| `email` | Must not already exist in `users` table | "An account with this email address already exists." |
| `password` | Min 8 characters, max 128 characters | "Password must be at least 8 characters long." |

---

## 11. Error States and Edge Cases

- **Existing Email:** When a user registers with an email that already exists, return friendly message: "An account with this email address already exists."
- **Whitespace Only Name:** If user enters spaces only for `name`, reject with "Please provide your full name."
- **Password Too Short:** If password is under 8 characters, reject with "Password must be at least 8 characters long."
- **Database Connection Error:** Handle database errors gracefully, logging error internally and returning a general message: "An unexpected error occurred. Please try again."
- **Already Logged-in User:** If user is already authenticated in session, redirect from `/register` directly to the dashboard/expenses view.

---

## 12. Acceptance Criteria

1. **GET Request:** Visiting `/register` renders the registration form with full name, email, and password inputs and a submit button.
2. **Missing Fields:** Submitting with empty fields displays an appropriate error banner and preserves valid inputs.
3. **Short Password:** Submitting a password shorter than 8 characters returns "Password must be at least 8 characters long."
4. **Duplicate Email:** Submitting an email already present in the database returns "An account with this email address already exists."
5. **Successful Registration:** Submitting valid name, unique email, and >= 8 character password:
   - Hashes password (no plaintext in SQLite).
   - Inserts row into `users` table.
   - Redirects to `/login` with success message (or auto-logs in).
6. **Case-Insensitive Email:** User registered as `john@example.com` cannot re-register as `John@Example.com`.
7. **Accessibility:** Form fields and errors are accessible to screen readers and keyboard navigation.

---

## 13. Testing and Verification Plan

### 13.1 Automated Tests (`tests/test_auth.py`)
- `test_register_page_loads`: `GET /register` returns status code 200 with form elements.
- `test_register_successful`: Submitting valid details creates user in SQLite and redirects.
- `test_register_duplicate_email`: Attempting to register twice with same email returns error.
- `test_register_short_password`: Attempting to register with < 8 chars password fails validation.
- `test_register_empty_name`: Submitting empty name fails validation.
- `test_password_is_hashed`: Verifies stored `password_hash` is not plaintext and verifies with `check_password_hash`.

### 13.2 Manual Verification
- Run `./venv/bin/pytest tests/test_auth.py`
- Run local server `python app.py` on port 5001.
- Manually test registration in browser, verifying error messages and successful redirect.

---

## 14. Implementation Plan Broken into Small, Ordered Tasks

1. **Database Foundation (`database/db.py`):**
   - Implement `get_db()` and `init_db()` creating the `users` table and email unique index.
2. **Backend Route Logic (`app.py`):**
   - Update `@app.route("/register", methods=["GET", "POST"])` to process form submissions.
   - Implement validation for `name`, `email`, and `password`.
   - Implement password hashing via `werkzeug.security.generate_password_hash`.
   - Insert new user into database and handle unique constraint collisions.
   - Redirect to `/login` with flash message.
3. **Template Enhancement (`templates/register.html`):**
   - Update input fields to preserve `name` and `email` on validation errors (`value="{{ name }}"`, `value="{{ email }}"`).
   - Add `minlength="8"` and `role="alert"` for accessibility.
4. **Automated Testing:**
   - Create `tests/test_auth.py` covering registration test cases.
   - Execute tests with `./venv/bin/pytest`.

---

## 15. Relevant Existing Files and Proposed Changes

- **Files to Modify:**
  - `@app.py`: Update `/register` route to handle `POST`, validate data, hash password, and query SQLite.
  - `@database/db.py`: Implement `get_db()`, `init_db()`, and create `users` table schema.
  - `@templates/register.html`: Add value retention and client-side validation hints.
- **Files to Create:**
  - `specs/user-registration.md`: This feature specification document.
  - `@tests/test_auth.py`: Pytest test suite for user registration and authentication.

---

## 16. Dependencies, Risks, Assumptions, and Open Questions

- **Dependencies:**
  - `werkzeug.security` for password hashing (already present in `requirements.txt`).
  - SQLite database initialized before registration requests run.
- **Assumptions:**
  - Registration redirects to `/login` where user must enter their credentials to establish a session (standard pattern).
  - No email verification/activation link required for this stage of Spendly.
- **Open Questions:**
  - Should the user be automatically logged in upon successful registration, or redirected to `/login` to sign in? *(Recommendation: Redirect to `/login` with a success alert for clarity, or auto-login if a frictionless onboarding flow is preferred).*
