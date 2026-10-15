# Feature Specification: User Profile Page Design & Account Settings

## 1. Feature Title and Summary

- **Feature Name:** User Profile Page Design and Account Management
- **Target Specification File:** `specs/profile-page-design.md`
- **Summary:** Design and implement a dedicated, authenticated Profile Page (`@templates/profile.html`) and associated backend controller logic (`@app.route("/profile")` in `@app.py`). The profile page serves as the user's personal hub in Spendly, featuring an editorial user summary card (initials avatar, member-since date, verified email badge), an account summary section, an intuitive profile editing interface for updating name and email, and a secure password change mechanism. All components strictly adhere to Spendly's warm paper aesthetic, typography guidelines, and accessibility standards.

---

## 2. Problem Statement

Currently in Spendly:
1. Navigating to the Profile link in `@templates/base.html` routes to `@app.route("/profile")`, which only returns a plain text placeholder string: `"Profile page — coming in Step 4"`.
2. Authenticated users have no visual dashboard or settings area to inspect their account details, member tenure, or spending statistics overview.
3. Users cannot update their profile information (such as correcting a misspelled name or updating their email address) once registered.
4. Users have no self-service mechanism to change or rotate their account password.
5. In `@app.py`, the `load_logged_in_user` hook selects only `id, name, email` from `users`, omitting `created_at`, which is necessary to display user account longevity and membership history.
6. There is no dedicated stylesheet section in `@static/css/style.css` or template file in `@templates/` to provide a cohesive profile UI matching the landing and auth page aesthetics.

---

## 3. Goals and Expected Outcomes

- **Deliver an Editorial Profile Interface:** Create `@templates/profile.html` extending `@templates/base.html`, adhering to Spendly's warm paper palette (`--paper`, `--paper-card`, `--ink`, `--accent`), serif typography (`--font-display`), and clean layout hierarchy.
- **Display User Identity & Monogram Avatar:** Render a clean visual header with the user's initials generated dynamically, full display name, normalized email, and human-formatted registration date (e.g., "Member since October 2026").
- **Account Activity & Quick Metrics Preview:** Provide an overview summary grid showing high-level account status (e.g., Account Status: Active, Currency: INR (₹), Total Tracked Expenses count).
- **Personal Information Management:** Allow users to update their full name and email address with proper input sanitization, duplicate email detection, and database persistence.
- **Secure Password Rotation:** Provide a dedicated security card where users can change their password by validating their current password, enforcing minimum length (8 characters), and verifying password confirmation.
- **Preserve Existing Architecture & Separation of Concerns:**
  - Route handlers and validation in `@app.py`.
  - Presentation and layout in `@templates/profile.html`.
  - Reusable CSS classes in `@static/css/style.css` (no inline styles).
  - Client-side enhancements in `@static/js/main.js` if necessary (e.g. tab switching or inline confirmation).
- **Comprehensive Test Coverage:** Add automated pytest cases in `tests/test_profile.py` verifying authorization, rendering, form validations, successful updates, password verification, and error boundaries.

---

## 4. Target Users and User Stories

- **Target User:** Authenticated Spendly users managing their personal finance account on mobile, tablet, or desktop devices.
- **User Stories:**
  - *As an authenticated user*, I want to view my profile details (name, email, membership date) in a beautifully formatted page so that I can verify my account status.
  - *As a user who made a typo during sign up*, I want to update my name so that the application greets me properly.
  - *As a user changing email providers*, I want to update my email address without losing my existing account or transaction history.
  - *As a security-conscious user*, I want to change my account password by providing my current password and choosing a new secure password.
  - *As an unauthenticated user*, if I attempt to visit `/profile`, I should be redirected to the sign-in page with a friendly flash message and return directly to the profile page after authenticating.
  - *As a mobile user*, I want the profile layout and form cards to stack cleanly and remain fully accessible with touch-friendly controls.

---

## 5. Functional Requirements

### 5.1 Route Access and Authorization (`GET /profile`)
- **Route:** `@app.route("/profile", methods=["GET"])`
- **Protection:** Decorated with `@login_required`.
- **Session Verification:**
  - If `g.user is None`, redirect to `url_for("login", next=request.path)` with flash message `"Please sign in to access this page."`.
- **Data Retrieval:**
  - Query current user's full record from SQLite:
    ```sql
    SELECT id, name, email, created_at FROM users WHERE id = ?
    ```
  - Fetch account summary data (e.g. transaction count from `expenses` table if existing, or default count `0` safely).
- **Rendering Context:**
  - Render `@templates/profile.html` passing `user=user`, `initials=initials`, and flash messages.

### 5.2 Profile Information Update (`POST /profile/update`)
- **Route:** `@app.route("/profile/update", methods=["POST"])` (or consolidated into `@app.route("/profile", methods=["GET", "POST"])` with action dispatching).
- **Protection:** `@login_required`.
- **Input Parameters:**
  - `name`: String, trimmed. Required, length 2 to 100 characters.
  - `email`: String, trimmed and lowercased. Required, valid email format regex (`^[^@\s]+@[^@\s]+\.[^@\s]+$`), maximum 255 characters.
- **Validation Rules:**
  - If `name` is empty or invalid: Flash error `"Please provide your full name (2–100 characters)."` and return to profile.
  - If `email` is invalid: Flash error `"Please provide a valid email address."` and return to profile.
  - If `email` differs from `g.user["email"]`:
    - Query database to check if email is already taken:
      ```sql
      SELECT id FROM users WHERE email = ? AND id != ?
      ```
    - If found: Flash error `"An account with this email address already exists."` and return.
- **Persistence:**
  - Update `users` table:
    ```sql
    UPDATE users SET name = ?, email = ? WHERE id = ?
    ```
  - Commit transaction.
  - Update `session["user_name"] = name`.
  - Flash success notification: `"Your profile details have been updated."` (`category="success"`).
  - Redirect to `url_for("profile")`.

### 5.3 Password Change (`POST /profile/change-password`)
- **Route:** `@app.route("/profile/change-password", methods=["POST"])` (or modular action within `/profile`).
- **Protection:** `@login_required`.
- **Input Parameters:**
  - `current_password`: String, required.
  - `new_password`: String, required, length 8 to 128 characters.
  - `confirm_password`: String, required, must match `new_password`.
- **Validation Rules:**
  - If any field is missing: Flash error `"All password fields are required."`.
  - Fetch user's current `password_hash` from database:
    ```sql
    SELECT password_hash FROM users WHERE id = ?
    ```
  - Verify current password using `check_password_hash(user["password_hash"], current_password)`.
    - If `False`: Flash error `"Current password is incorrect."`.
  - Validate new password length (8 to 128 characters):
    - If invalid: Flash error `"New password must be at least 8 characters long."`.
  - Verify match between `new_password` and `confirm_password`:
    - If `new_password != confirm_password`: Flash error `"New passwords do not match."`.
  - Prevent reusing the exact same password:
    - If `check_password_hash(user["password_hash"], new_password)` is `True`: Flash error `"New password must be different from your current password."`.
- **Persistence:**
  - Generate hash: `new_hash = generate_password_hash(new_password)`.
  - Update `users` table:
    ```sql
    UPDATE users SET password_hash = ? WHERE id = ?
    ```
  - Commit transaction.
  - Flash success message: `"Password changed successfully."` (`category="success"`).
  - Redirect to `url_for("profile")`.

---

## 6. UI/UX Design & Component Hierarchy

### 6.1 Layout Overview
The Profile Page is centered within Spendly's standard container (`--max-width: 1200px` with an inner content width of `--profile-width: 960px`). It uses a structured two-column layout on desktop and collapses into an intuitive single-column stack on tablets and mobile screens.

```
+-----------------------------------------------------------------------+
|  Navbar (Brand "◈ Spendly" | Profile (Active) | Sign out)              |
+-----------------------------------------------------------------------+
|                                                                       |
|  [Flash Notifications: Success / Error Messages]                      |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  | PROFILE HEADER HERO CARD                                         |  |
|  | +--------+  Nitish Kumar                     [ Member Badge ]   |  |
|  | |   NK   |  nitish@example.com                                  |  |
|  | +--------+  ◈ Member since October 2026                         |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|  +---------------------------+  +----------------------------------+  |
|  | QUICK STATS SUMMARY       |  | EDIT PERSONAL INFORMATION        |  |
|  |                           |  |                                  |  |
|  | [◈ Active Status]         |  | Full Name                        |  |
|  | Registered & Active       |  | [ Nitish Kumar                ]  |  |
|  |                           |  |                                  |  |
|  | [₹ Currency]              |  | Email Address                    |  |
|  | Indian Rupee (INR)        |  | [ nitish@example.com          ]  |  |
|  |                           |  |                                  |  |
|  | [◷ Joined Date]           |  | [ Save Profile Changes ]         |  |
|  | Oct 15, 2026              |  +----------------------------------+  |
|  +---------------------------+                                        |
|                                 +----------------------------------+  |
|  +---------------------------+  | SECURITY & PASSWORD              |  |
|  | ACCOUNT ACTIONS           |  |                                  |  |
|  |                           |  | Current Password                 |  |
|  | - Sign out of Spendly     |  | [ **************************  ]  |  |
|  | - Return to Dashboard     |  |                                  |  |
|  +---------------------------+  | New Password (min 8 chars)       |  |
|                                 | [ **************************  ]  |  |
|                                 |                                  |  |
|                                 | Confirm New Password             |  |
|                                 | [ **************************  ]  |  |
|                                 |                                  |  |
|                                 | [ Update Password ]              |  |
|                                 +----------------------------------+  |
|                                                                       |
+-----------------------------------------------------------------------+
|  Footer (Brand "◈ Spendly" | Terms & Privacy Modals)                  |
+-----------------------------------------------------------------------+
```

### 6.2 Component Specifications

#### A. Profile Header Card (`.profile-header-card`)
- **Container:** Rounded card (`background: var(--paper-card); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 2rem;`).
- **Avatar Monogram (`.profile-avatar`):**
  - Dimension: `72px x 72px` (desktop), `60px x 60px` (mobile).
  - Background: `var(--accent-light)` (#e8f0eb).
  - Border: `2px solid var(--border-soft)`.
  - Typography: `var(--font-display)` or `var(--font-body)` bold, font-size `1.5rem`, color `var(--accent)` (#1a472a).
  - Computation: First letters of first and last name (e.g., "Jane Doe" -> "JD", "Nitish" -> "N").
- **Header Details:**
  - Name: `font-family: var(--font-display); font-size: 1.75rem; color: var(--ink); margin: 0;`.
  - Email: `font-size: 0.95rem; color: var(--ink-muted);`.
  - Member Badge (`.profile-badge`): Small pill tag (`background: var(--paper-warm); border: 1px solid var(--border); color: var(--ink-soft); font-size: 0.75rem; padding: 0.25rem 0.65rem; border-radius: 999px;`).

#### B. Quick Stats / Account Information (`.profile-sidebar`)
- **Metric Cards (`.profile-stat-box`):**
  - Clean cards showing metadata:
    1. Account Status: "Active Account" with a small green dot indicator (`var(--accent)`).
    2. Primary Currency: "INR (₹)" representing default financial tracking currency.
    3. Account Created: Formatted date string (e.g., "15 Oct 2026").
- **Quick Navigation Links:**
  - Clean secondary links: "View Transactions" (links to landing or future dashboard), "Sign Out" button/link with confirmation styling.

#### C. Personal Information Card (`.profile-content-card`)
- Standard Spendly form controls matching `@templates/login.html` and `@templates/register.html`:
  - `label`: `font-size: 0.85rem; font-weight: 500; color: var(--ink-soft);`.
  - `input.form-input`: `background: var(--paper); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 0.6rem 0.875rem;`.
  - Submit Button (`.btn-primary` or `.btn-submit`): `background: var(--ink); color: var(--paper);` with `:hover` state transition to `var(--accent)`.

#### D. Security & Password Card (`.profile-content-card`)
- Distinct card for credential isolation.
- Inputs for `current_password`, `new_password`, `confirm_password`.
- Informative helper text: "Password must be at least 8 characters long." (`font-size: 0.8rem; color: var(--ink-faint);`).

### 6.3 Design Tokens Used
- **Colors:**
  - Backgrounds: `--paper` (`#f7f6f3`), `--paper-card` (`#ffffff`), `--paper-warm` (`#f0ede6`).
  - Typography: `--ink` (`#0f0f0f`), `--ink-soft` (`#2d2d2d`), `--ink-muted` (`#6b6b6b`), `--ink-faint` (`#a0a0a0`).
  - Accents: `--accent` (`#1a472a`), `--accent-light` (`#e8f0eb`), `--accent-2` (`#c17f24`).
  - Alerts: `--danger` (`#c0392b`), `--danger-light` (`#fdecea`).
  - Borders: `--border` (`#e4e1da`), `--border-soft` (`#eeebe4`).
- **Radii:** `--radius-sm` (`6px`), `--radius-md` (`12px`), `--radius-lg` (`20px`).
- **Typography:** `--font-display` ('DM Serif Display', Georgia, serif), `--font-body` ('DM Sans', system-ui, sans-serif).

---

## 7. Backend, Routes, and Controller Logic

### 7.1 Existing Code Inspection
In `@app.py`:
- Line 18–29:
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
- Line 31–38:
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
- Line 166–169:
  ```python
  @app.route("/profile")
  @login_required
  def profile():
      return "Profile page — coming in Step 4"
  ```

### 7.2 Proposed Backend Implementation Plan

#### Option A: Unified Route Handling (`GET` and `POST` on `/profile`)
Consolidated in `@app.route("/profile", methods=["GET", "POST"])`:
- When `request.method == "POST"`:
  - Check `action = request.form.get("action")`:
    - If `action == "update_profile"`: Execute Profile Update flow.
    - If `action == "change_password"`: Execute Password Change flow.
- When `request.method == "GET"`:
  - Fetch detailed user record including `created_at`.
  - Format initials helper:
    ```python
    def get_initials(name):
        parts = name.strip().split()
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()
    ```
  - Format `created_at` date:
    ```python
    # Format e.g. "October 2026" or "15 Oct 2026"
    ```
  - Render `@templates/profile.html`.

*Advantages of Option A:* Keeps all profile actions under a single RESTful endpoint, handles flash messages seamlessly, and matches existing Spendly conventions in `register` and `login`.

---

## 8. Database and Data-Model Considerations

### 8.1 Schema Verification
The `users` table in `@database/db.py` currently contains:
```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
- **Conclusion:** No database schema migration is required. All necessary fields (`id`, `name`, `email`, `password_hash`, `created_at`) are already defined and populated in SQLite.
- **Query Optimization:** Update the query in `load_logged_in_user` or the profile controller to select `created_at`:
  ```sql
  SELECT id, name, email, created_at FROM users WHERE id = ?
  ```

---

## 9. Validation, Authorization, and Security

1. **Authentication Requirement:**
   - The profile view and any modification actions MUST be guarded by `@login_required`.
   - Any unauthenticated request redirects to `/login?next=%2Fprofile`.
2. **Current Password Re-Authentication:**
   - Password changes MUST require the existing password to prevent account takeover in cases of unattended active browser sessions.
3. **Session Fixation & Data Integrity:**
   - When a user's name is updated, update `session["user_name"] = new_name` so any navbar references immediately reflect the change.
   - Do not invalidate the session cookie on simple name/email edits.
   - Optionally, upon successful password change, keep the user logged in and flash a success notification.
4. **Email Uniqueness & Normalization:**
   - Emails must be lowercased and stripped before checking uniqueness and saving.
   - SQL query must explicitly exclude `current_user_id` (`WHERE email = ? AND id != ?`) to allow users to update their name while keeping the same email.
5. **Length and Regex Boundaries:**
   - Name: Min 2, max 100 characters.
   - Email: Min 5, max 255 characters, valid email regex.
   - Password: Min 8, max 128 characters.
6. **Open Redirect Protection:**
   - Existing redirect logic in `/login` (`next_url.startswith("/") and not next_url.startswith("//")`) ensures safe return to `/profile`.

---

## 10. Error States and Edge Cases

| Scenario / Edge Case | Expected System Behavior | User Feedback |
| :--- | :--- | :--- |
| **Unauthenticated User accesses `/profile`** | Redirect HTTP 302 to `/login?next=/profile` | Flash: `"Please sign in to access this page."` |
| **Submitting empty name** | HTTP 200 re-render or 302 redirect to `/profile` | Flash error: `"Please provide your full name (2–100 characters)."` |
| **Submitting invalid email syntax** | Reject update | Flash error: `"Please provide a valid email address."` |
| **Updating email to an address used by another user** | SQLite check detects collision | Flash error: `"An account with this email address already exists."` |
| **Updating name while leaving email unchanged** | SQLite check permits unchanged email for same `user_id` | Flash success: `"Your profile details have been updated."` |
| **Password change with incorrect current password** | `check_password_hash` fails; no changes saved | Flash error: `"Current password is incorrect."` |
| **New password shorter than 8 characters** | Validation fails before hashing | Flash error: `"New password must be at least 8 characters long."` |
| **New password and confirmation mismatch** | Validation fails | Flash error: `"New passwords do not match."` |
| **New password is identical to current password** | Checked via `check_password_hash`; rejected | Flash error: `"New password must be different from your current password."` |
| **Single-word user name (e.g., "Cher")** | Initials helper handles single word safely | Generates "CH" or "C" without index out-of-range errors |
| **Special characters in user name** | Template auto-escapes HTML | Safely displayed without XSS |

---

## 11. Acceptance Criteria

- [ ] **AC-1:** Navigating to `/profile` while logged in returns an HTTP 200 response and renders `@templates/profile.html`.
- [ ] **AC-2:** Navigating to `/profile` while logged out redirects to `/login` with an informative flash message.
- [ ] **AC-3:** The profile page displays the user's name, email, monogram initials avatar, and member-since date.
- [ ] **AC-4:** The user can update their display name and email address; successful updates reflect in the database and update `session["user_name"]`.
- [ ] **AC-5:** Attempting to change email to an already registered email address is rejected with an error notification.
- [ ] **AC-6:** The user can change their password by supplying the correct current password and a valid new password.
- [ ] **AC-7:** Entering an incorrect current password rejects the password change and displays a clear error message.
- [ ] **AC-8:** Entering mismatched new passwords or passwords shorter than 8 characters displays appropriate error messages.
- [ ] **AC-9:** The page is fully responsive, looking balanced on desktop (>900px), tablet (600px–900px), and mobile (<600px).
- [ ] **AC-10:** All styling conforms to Spendly's design tokens and guidelines in `@static/css/style.css` (no inline styles).
- [ ] **AC-11:** Automated pytest suite in `tests/test_profile.py` passes with 100% test success.

---

## 12. Testing and Verification Plan

### 12.1 Automated Test Suite (`tests/test_profile.py`)
Create a comprehensive test file using pytest and Flask test client:
1. `test_profile_access_unauthenticated`:
   - `client.get("/profile")` -> 302 redirect to `/login?next=%2Fprofile`.
2. `test_profile_access_authenticated`:
   - Authenticate client session.
   - `client.get("/profile")` -> 200 OK.
   - Assert presence of user's name, email, monogram avatar, and "Member since" text.
3. `test_update_profile_success`:
   - Post valid updated name and email.
   - Assert database row updated.
   - Assert success flash message.
4. `test_update_profile_duplicate_email`:
   - Create User A and User B.
   - User B attempts to change email to User A's email.
   - Assert error flash message and no database change for User B.
5. `test_update_profile_validation_errors`:
   - Empty name, blank email, malformed email.
   - Assert corresponding validation errors.
6. `test_change_password_success`:
   - Post correct current password, valid new password matching confirmation.
   - Verify updated `password_hash` in database.
   - Verify user can log in with new password.
7. `test_change_password_wrong_current`:
   - Post incorrect current password.
   - Assert error flash message and `password_hash` unchanged.
8. `test_change_password_mismatch_and_length`:
   - Test short password (<8 chars) and mismatched confirmation.
   - Assert proper error messages.

### 12.2 Manual Verification
- Log in with test user in local browser (`http://localhost:5001/login`).
- Click "Profile" in the navigation bar.
- Verify visual aesthetic, font rendering, borders, and monogram avatar.
- Submit profile update with new name -> verify top nav and greeting updates.
- Test responsive viewports using Chrome DevTools (Desktop 1200px, Tablet 768px, Mobile 375px).
- Run `./venv/bin/pytest` to ensure all existing and new tests pass cleanly.

---

## 13. Implementation Plan Broken into Small Tasks

1. **Task 1: Profile Route & Context Enhancement in `@app.py`**
   - Update `load_logged_in_user` to select `created_at` alongside `id, name, email`.
   - Implement initials generator helper function.
   - Implement `GET /profile` view in `@app.py` rendering `profile.html`.
2. **Task 2: Profile Page Template Creation (`@templates/profile.html`)**
   - Create `@templates/profile.html` extending `base.html`.
   - Build Header Card with monogram avatar, user details, and member badge.
   - Build Sidebar with Account Quick Stats & Quick Actions.
   - Build Personal Information form (`name`, `email`).
   - Build Security form (`current_password`, `new_password`, `confirm_password`).
3. **Task 3: Styling in `@static/css/style.css`**
   - Add profile layout grid (`.profile-container`, `.profile-grid`, `.profile-sidebar`, `.profile-main`).
   - Style avatar monogram (`.profile-avatar`), header card (`.profile-header-card`), and badge (`.profile-badge`).
   - Style form cards (`.profile-card`), section headers, input rows, and button groups.
   - Add responsive rules for `<900px` and `<600px` viewports.
4. **Task 4: Profile Update & Password Change Controller Logic in `@app.py`**
   - Implement `POST` handling for profile updates with validation and duplicate email check.
   - Implement `POST` handling for password changes with current hash verification.
5. **Task 5: Test Suite Implementation (`tests/test_profile.py`)**
   - Write pytest cases covering all user stories and edge cases.
   - Run `./venv/bin/pytest` and verify full test passage.

---

## 14. Relevant Existing Files and Proposed File Changes

| File | Status | Description of Proposed Changes |
| :--- | :--- | :--- |
| `@app.py` | Existing (Modify) | Update `load_logged_in_user` to include `created_at`; replace placeholder `def profile()` with complete `GET` and `POST` handlers for profile data and password rotation. |
| `@templates/base.html` | Existing (Preserve) | Already contains dynamic link to `{{ url_for('profile') }}` when `g.user` is present. Set active nav indicator if desired. |
| `@templates/profile.html` | New (Create) | User profile template extending `base.html` with avatar, details, edit form, security card, and statistics. |
| `@static/css/style.css` | Existing (Modify) | Add profile container, grid layout, avatar monogram, stat boxes, and responsive rules using existing design tokens. |
| `@database/db.py` | Existing (No Change) | `users` schema already has `id, name, email, password_hash, created_at`. No migration required. |
| `tests/test_profile.py` | New (Create) | Automated unit and integration tests for profile page authorization, updating personal info, and password change logic. |

---

## 15. Dependencies, Risks, Assumptions, and Open Questions

### 15.1 Assumptions
- SQLite database has active foreign keys and `created_at` timestamp populated for existing users.
- Sessions use the standard Flask client-side signed cookies configured via `app.secret_key`.
- No email verification service (SMTP) is currently configured; email changes take effect immediately upon form submission.

### 15.2 Risks
- **Duplicate Email Conflicts:** If validation does not exclude the user's own `user_id`, updating only the name would falsely trigger a duplicate email error. (Mitigated by explicit SQL: `WHERE email = ? AND id != ?`).
- **Session Desynchronization:** If `session["user_name"]` is not updated when the name changes, navbar greetings might show stale data until re-login. (Mitigated by re-assigning `session["user_name"] = name` on save).

### 15.3 Open Questions for Consideration
- *Avatar Uploads:* Should Spendly support custom image uploads (e.g. JPG/PNG via file upload), or is a procedural monogram avatar (initials circle) preferred to avoid media storage dependencies? (Specification assumes procedural monogram avatar in alignment with minimal dependencies).
- *Account Deletion ("Danger Zone"):* Should an option to delete the account and associated expenses be added in this phase or deferred to a subsequent milestone? (Recommended: defer account deletion to a dedicated GDPR/Account Management milestone to keep this scope focused on profile viewing and editing).
