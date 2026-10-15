# Feature Specification: User Profile Page Design & Account Settings

## 1. Feature Title and Summary

- **Feature Name:** User Profile Page Design and Account Management
- **Target Specification File:** `specs/profile-page-design.md`
- **Summary:** Design and implement a dedicated, authenticated Profile Page (`@templates/profile.html`) and associated backend controller logic (`@app.route("/profile")` in `@app.py`). The profile page serves as the user's personal hub in Spendly, featuring an editorial user summary card (initials avatar, member-since date, verified email badge), an account summary section, a **Recent Expenses** section (displaying category, description, date, and amount with an empty state fallback), an intuitive profile editing interface for updating name and email, and a secure password change mechanism. All components strictly adhere to Spendly's warm paper aesthetic, typography guidelines, and accessibility standards.

---

## 2. Problem Statement

Currently in Spendly:
1. Navigating to the Profile link in `@templates/base.html` routes to `@app.route("/profile")`, which only returns a plain text placeholder string or basic profile without financial context.
2. Authenticated users cannot review their recent financial transactions on their profile page—the profile **does not display recent expenses with category, description, date, and amount**, leaving users disconnected from their recent spending activity.
3. Authenticated users have no visual dashboard or settings area to inspect their account details, member tenure, or spending statistics overview.
4. Users cannot update their profile information (such as correcting a misspelled name or updating their email address) once registered.
5. Users have no self-service mechanism to change or rotate their account password.
6. In `@app.py`, the `load_logged_in_user` hook selects only `id, name, email` from `users`, omitting `created_at`, which is necessary to display user account longevity and membership history.
7. There is no dedicated stylesheet section in `@static/css/style.css` or template file in `@templates/` to provide a cohesive profile UI matching the landing and auth page aesthetics.

---

## 3. Goals and Expected Outcomes

- **Deliver an Editorial Profile Interface:** Create `@templates/profile.html` extending `@templates/base.html`, adhering to Spendly's warm paper palette (`--paper`, `--paper-card`, `--ink`, `--accent`), serif typography (`--font-display`), and clean layout hierarchy.
- **Display User Identity & Monogram Avatar:** Render a clean visual header with the user's initials generated dynamically, full display name, normalized email, and human-formatted registration date (e.g., "Member since October 2026").
- **Display Recent Expenses Feed:** Prominently showcase the user's recent transactions on the profile page, including:
  - **Category:** Tagged with clean badge styling (e.g., Travel, Food, Bills, Health, Entertainment).
  - **Description:** Clear textual context of what was purchased.
  - **Date:** Human-readable formatted date string (e.g., "14 Oct 2026").
  - **Amount:** Formatted with currency prefix and precision (e.g., "₹450.00").
  - **Empty State:** A warm, friendly callout when the user has not logged any expenses yet.
- **Account Activity & Quick Metrics Preview:** Provide an overview summary grid showing high-level account status (e.g., Account Status: Active, Currency: INR (₹), Total Tracked Expenses count).
- **Personal Information Management:** Allow users to update their full name and email address with proper input sanitization, duplicate email detection, and database persistence.
- **Secure Password Rotation:** Provide a dedicated security card where users can change their password by validating their current password, enforcing minimum length (8 characters), and verifying password confirmation.
- **Preserve Existing Architecture & Separation of Concerns:**
  - Route handlers and validation in `@app.py`.
  - Presentation and layout in `@templates/profile.html`.
  - Reusable CSS classes in `@static/css/style.css` (no inline styles).
  - Client-side enhancements in `@static/js/main.js` if necessary.
- **Comprehensive Test Coverage:** Add automated pytest cases in `tests/test_profile.py` verifying authorization, rendering, recent expenses feed with category/description/date/amount, empty states, form validations, successful updates, password verification, and error boundaries.

---

## 4. Target Users and User Stories

- **Target User:** Authenticated Spendly users managing their personal finance account on mobile, tablet, or desktop devices.
- **User Stories:**
  - *As an authenticated user*, I want to view my recent expenses (category, description, date, and amount) on my profile page so that I can immediately see my latest spending patterns without digging through multiple pages.
  - *As a new user with no expenses*, I want to see an inviting empty state on my profile explaining how to start logging expenses.
  - *As an authenticated user*, I want to view my profile details (name, email, membership date) in a beautifully formatted page so that I can verify my account status.
  - *As a user who made a typo during sign up*, I want to update my name so that the application greets me properly.
  - *As a user changing email providers*, I want to update my email address without losing my existing account or transaction history.
  - *As a security-conscious user*, I want to change my account password by providing my current password and choosing a new secure password.
  - *As an unauthenticated user*, if I attempt to visit `/profile`, I should be redirected to the sign-in page with a friendly flash message and return directly to the profile page after authenticating.
  - *As a mobile user*, I want the profile layout, expense list, and form cards to stack cleanly and remain fully accessible with touch-friendly controls.

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
  - Query current user's recent expenses (ordered by latest date and id descending, limit 5):
    ```sql
    SELECT id, category, description, date, amount
    FROM expenses
    WHERE user_id = ?
    ORDER BY date DESC, id DESC
    LIMIT 5
    ```
  - Fetch total expense count and summary sum for the account quick stats.
- **Rendering Context:**
  - Render `@templates/profile.html` passing `user=user`, `initials=initials`, `recent_expenses=recent_expenses`, `total_expenses=total_expenses`, and flash messages.

### 5.2 Recent Expenses Feed (`GET /profile`)
- **Requirement:** The profile page must display the user's latest expenses with the following columns/elements:
  1. **Category:** Visual pill badge with category name (e.g., Food, Travel, Bills, Shopping, Health).
  2. **Description:** Clear title/description of the expense transaction (e.g., "Grocery shopping at supermarket", "Metro recharge").
  3. **Date:** Formatted transaction date (e.g., "14 Oct 2026").
  4. **Amount:** Monetary value formatted in Indian Rupees with two decimal places (e.g., "₹1,250.00").
- **Ordering:** Strictly ordered by transaction date descending, then primary key ID descending (`ORDER BY date DESC, id DESC`).
- **Data Isolation:** Only expenses matching `user_id = g.user["id"]` are retrieved.
- **Empty State Behavior:**
  - If the user has 0 logged expenses (`recent_expenses` list is empty):
    - Render an empty state card (`.expenses-empty-card`) with an icon, heading ("No expenses logged yet"), descriptive guidance ("Your recent expenses will appear here once you start logging transactions."), and a CTA button linking to `/expenses/add` ("Log your first expense").

### 5.3 Profile Information Update (`POST /profile`)
- **Route:** `@app.route("/profile", methods=["POST"])` with `action="update_profile"`.
- **Protection:** `@login_required`.
- **Input Parameters:**
  - `name`: String, trimmed. Required, length 2 to 100 characters.
  - `email`: String, trimmed and lowercased. Required, valid email format regex (`^[^@\s]+@[^@\s]+\.[^@\s]+$`), maximum 255 characters.
- **Validation Rules:**
  - If `name` is empty or invalid: Flash error `"Please provide your full name (2–100 characters)."` and redirect to `/profile`.
  - If `email` is invalid: Flash error `"Please provide a valid email address."` and redirect to `/profile`.
  - If `email` differs from `g.user["email"]`:
    - Query database to check if email is already taken by another account:
      ```sql
      SELECT id FROM users WHERE email = ? AND id != ?
      ```
    - If found: Flash error `"An account with this email address already exists."` and redirect.
- **Persistence:**
  - Update `users` table:
    ```sql
    UPDATE users SET name = ?, email = ? WHERE id = ?
    ```
  - Commit transaction.
  - Update `session["user_name"] = name`.
  - Flash success notification: `"Your profile details have been updated."` (`category="success"`).
  - Redirect to `url_for("profile")`.

### 5.4 Password Change (`POST /profile`)
- **Route:** `@app.route("/profile", methods=["POST"])` with `action="change_password"`.
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
+-----------------------------------------------------------------------------------+
|  Navbar (Brand "◈ Spendly" | Profile (Active) | Sign out)                         |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [Flash Notifications: Success / Error Messages]                                  |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | PROFILE HEADER HERO CARD                                                     |  |
|  | +--------+  Nitish Kumar                                 [ Active Member ]  |  |
|  | |   NK   |  nitish@example.com                                              |  |
|  | +--------+  ◈ Member since October 2026                                     |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
|  +---------------------------+  +----------------------------------------------+  |
|  | QUICK STATS & ACTIONS     |  | RECENT EXPENSES                              |  |
|  |                           |  | Category   Description       Date     Amount |  |
|  | [◈ Active Status]         |  |----------------------------------------------|  |
|  | Registered & Active       |  | [Food]     Weekly Groceries  14 Oct  ₹1,250  |  |
|  |                           |  | [Travel]   Metro Card        12 Oct    ₹500  |  |
|  | [₹ Currency]              |  | [Bills]    Internet Bill     10 Oct    ₹899  |  |
|  | Indian Rupee (INR)        |  +----------------------------------------------+  |
|  |                           |                                                    |
|  | [◷ Joined Date]           |  +----------------------------------------------+  |
|  | Oct 15, 2026              |  | EDIT PERSONAL INFORMATION                    |  |
|  |                           |  | Full Name: [ Nitish Kumar                  ] |  |
|  | [Σ Total Expenses]        |  | Email:     [ nitish@example.com            ] |  |
|  | 3 logged                  |  | [ Save Changes ]                             |  |
|  |                           |  +----------------------------------------------+  |
|  | - Back to Home            |                                                    |
|  | - Sign out                |  +----------------------------------------------+  |
|  +---------------------------+  | SECURITY & PASSWORD                          |  |
|                                 | Current Password: [ ********************** ] |  |
|                                 | New Password:     [ ********************** ] |  |
|                                 | Confirm Password: [ ********************** ] |  |
|                                 | [ Update Password ]                          |  |
|                                 +----------------------------------------------+  |
|                                                                                   |
+-----------------------------------------------------------------------------------+
|  Footer (Brand "◈ Spendly" | Terms & Privacy Modals)                              |
+-----------------------------------------------------------------------------------+
```

### 6.2 Component Specifications

#### A. Profile Header Card (`.profile-header-card`)
- Rounded card with monogram avatar circle (`.profile-avatar`), user's display name (`.profile-name`), email address, active badge, and formatted membership date.

#### B. Recent Expenses Section (`.profile-expenses-card`)
- **Card Container:** Rounded card (`background: var(--paper-card); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 1.75rem; margin-bottom: 2rem;`).
- **Header:** Title ("Recent Expenses") and descriptive subtitle ("Your latest transactions logged across categories").
- **Table / Feed Layout (`.profile-expenses-table`):**
  - Semantic `<table>` element with accessible `<thead>` and `<tbody>`.
  - Column 1: **Category** — Styled with `.badge-category` pill using soft background tones (`var(--accent-light)` or `--accent-2-light`).
  - Column 2: **Description** — Primary text styling (`var(--ink)`), gracefully handling longer descriptions with text truncation or wrapping.
  - Column 3: **Date** — Formatted timestamp (`var(--ink-muted)`), right-aligned or neutral.
  - Column 4: **Amount** — Bold numeric display with `₹` symbol (`font-weight: 600; color: var(--ink); text-align: right;`).
- **Empty State Container (`.expenses-empty-card`):**
  - Rendered when user has 0 transactions.
  - Icon: `◈` in circular badge.
  - Title: "No expenses logged yet".
  - Text: "Your recent spending will be summarized here once you start tracking."
  - Action button: Secondary or primary button linking to `/expenses/add`.

#### C. Personal Information Card (`.profile-card`)
- Card containing display name and email inputs, submit button with `action="update_profile"`.

#### D. Security & Password Card (`.profile-card`)
- Card containing current password, new password (min 8 chars), and confirm password inputs with `action="change_password"`.

### 6.3 Design Tokens Used
- **Colors:** `--paper`, `--paper-card`, `--paper-warm`, `--ink`, `--ink-soft`, `--ink-muted`, `--accent`, `--accent-light`, `--accent-2`, `--border`, `--border-soft`, `--danger`.
- **Typography:** `--font-display` ('DM Serif Display', serif), `--font-body` ('DM Sans', sans-serif).
- **Radii:** `--radius-sm` (6px), `--radius-md` (12px), `--radius-lg` (20px).

---

## 7. Backend, Routes, and Controller Logic

### 7.1 Database Table Schema (`expenses`)
The SQLite database schema initialized in `@database/db.py` must support the `expenses` table:
```sql
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    date DATE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_id ON expenses (user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses (date);
```

### 7.2 Controller Query in `@app.py`
Inside the `@app.route("/profile", methods=["GET", "POST"])` handler:
```python
# Query recent 5 expenses for the current user
expenses_rows = db.execute(
    """
    SELECT id, category, description, date, amount
    FROM expenses
    WHERE user_id = ?
    ORDER BY date DESC, id DESC
    LIMIT 5
    """,
    (g.user["id"],)
).fetchall()

# Count total transactions for sidebar statistics
total_count = db.execute(
    "SELECT COUNT(*) as count FROM expenses WHERE user_id = ?",
    (g.user["id"],)
).fetchone()["count"]
```

### 7.3 Currency & Date Formatting Helpers
- **Amount Formatting:** Format floats to INR: `f"₹{amount:,.2f}"` (e.g. `1250.0` -> `₹1,250.00`).
- **Date Formatting:** Format date strings (e.g., `2026-10-14` -> `14 Oct 2026`).

---

## 8. Database and Data-Model Considerations

- **Table Creation:** The `expenses` table must be included in `init_db()` in `@database/db.py` so that development, testing, and production environments create it automatically upon application boot.
- **Foreign Key Constraint:** Enforces `FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE` with `PRAGMA foreign_keys = ON;`.
- **Index Support:** Indexes on `user_id` and `date` ensure sub-millisecond retrieval of recent expenses even as the dataset scales.

---

## 9. Validation, Authorization, and Security

1. **Strict User Scoping (Data Isolation):**
   - The query MUST always filter by `WHERE user_id = ?` using `g.user["id"]`.
   - Users must NEVER be able to view another user's expenses.
2. **Authentication Guard:**
   - Protected by `@login_required`.
3. **Escaping & XSS Prevention:**
   - All user-entered descriptions and categories must be escaped by Jinja2 auto-escaping.
4. **Current Password Re-Authentication:**
   - Password changes require verifying the existing password with `check_password_hash`.
5. **Email Uniqueness:**
   - Update queries exclude the user's own `user_id` (`WHERE email = ? AND id != ?`).

---

## 10. Error States and Edge Cases

| Scenario / Edge Case | Expected System Behavior | User Feedback |
| :--- | :--- | :--- |
| **User has 0 expenses** | Query returns empty list `[]` | Renders `.expenses-empty-card` with "No expenses logged yet" and CTA |
| **User has 1–5 expenses** | Renders table with all rows in descending date order | Complete table with Category, Description, Date, Amount |
| **User has >5 expenses** | Shows only the 5 most recent transactions | Table shows top 5; sidebar shows total count |
| **Expense with empty description** | Gracefully displays "—" or category name as fallback | Clear tabular display without awkward whitespace |
| **Expense with large amount (e.g. ₹1,00,000)** | Numeric format handles comma separators smoothly | Formatted as `₹100,000.00` |
| **Unauthenticated access to `/profile`** | Redirect 302 to `/login?next=/profile` | Flash: `"Please sign in to access this page."` |
| **Duplicate email on profile update** | Rejection before database write | Flash error: `"An account with this email address already exists."` |
| **Incorrect current password** | Rejection before password hash update | Flash error: `"Current password is incorrect."` |

---

## 11. Acceptance Criteria

- [ ] **AC-1:** Navigating to `/profile` while logged in returns an HTTP 200 response and renders `@templates/profile.html`.
- [ ] **AC-2:** Navigating to `/profile` while logged out redirects to `/login` with an informative flash message.
- [ ] **AC-3:** The profile page displays the user's name, email, monogram initials avatar, and member-since date.
- [ ] **AC-4:** The profile page displays a **Recent Expenses** section with columns for **Category, Description, Date, and Amount**.
- [ ] **AC-5:** Recent expenses are strictly scoped to the logged-in user and ordered by `date DESC, id DESC` (up to 5 recent items).
- [ ] **AC-6:** When a user has no logged expenses, a clean empty state card is displayed prompting them to log their first expense.
- [ ] **AC-7:** The user can update their display name and email address; successful updates reflect in the database and update `session["user_name"]`.
- [ ] **AC-8:** Attempting to change email to an already registered email address is rejected with an error notification.
- [ ] **AC-9:** The user can change their password by supplying the correct current password and a valid new password.
- [ ] **AC-10:** Entering an incorrect current password rejects the password change with a clear error message.
- [ ] **AC-11:** The page is fully responsive, looking balanced on desktop (>900px), tablet (600px–900px), and mobile (<600px).
- [ ] **AC-12:** All styling conforms to Spendly's design tokens and guidelines in `@static/css/style.css` (no inline styles).
- [ ] **AC-13:** Automated pytest suite in `tests/test_profile.py` passes with 100% test success, including tests for recent expenses.

---

## 12. Testing and Verification Plan

### 12.1 Automated Test Suite (`tests/test_profile.py`)
1. `test_profile_recent_expenses_display`:
   - Seed sample expenses for user (e.g., Food: "Lunch", Bills: "Electricity", Travel: "Cab").
   - Visit `/profile`.
   - Assert all categories, descriptions, dates, and amounts are present in the HTML.
2. `test_profile_recent_expenses_ordering_and_limit`:
   - Seed 7 expenses with different dates.
   - Assert only the 5 most recent expenses appear on the profile page in descending date order.
3. `test_profile_recent_expenses_user_isolation`:
   - User A logs an expense "User A Private Purchase".
   - User B logs in and views `/profile`.
   - Assert "User A Private Purchase" is NOT in User B's profile.
4. `test_profile_expenses_empty_state`:
   - New user with 0 expenses views `/profile`.
   - Assert "No expenses logged yet" is rendered.
5. `test_profile_access_unauthenticated`: Redirects to `/login?next=/profile`.
6. `test_profile_authenticated_view`: Asserts header details and monogram avatar.
7. `test_update_profile_success`: Name & email update.
8. `test_update_profile_duplicate_email`: Duplicate email collision detection.
9. `test_change_password_success`: Password rotation and subsequent login.
10. `test_change_password_wrong_current`: Rejection on incorrect current password.

### 12.2 Manual Verification
- Seed development database with user and sample expenses.
- Navigate to `/profile` in browser.
- Verify Recent Expenses table visually matches Spendly's design tokens and warm paper aesthetic.
- Verify amounts format as `₹...`.
- Test responsive view on mobile screen width (375px).

---

## 13. Implementation Plan Broken into Small Tasks

1. **Task 1: Expenses Schema in `@database/db.py`**
   - Add `CREATE TABLE IF NOT EXISTS expenses (...)` and indexes to `init_db()`.
2. **Task 2: Backend Query & Formatting in `@app.py`**
   - Query user's recent 5 expenses and total count in `profile()` view.
   - Pass `recent_expenses` list with formatted dates and currency amounts to template context.
3. **Task 3: Template Markup in `@templates/profile.html`**
   - Add Recent Expenses card with table (Category, Description, Date, Amount) and empty state card.
4. **Task 4: Stylesheet Rules in `@static/css/style.css`**
   - Style `.profile-expenses-table`, `.badge-category`, `.expense-amount`, and `.expenses-empty-card`.
   - Add responsive table rules for mobile viewports.
5. **Task 5: Test Coverage in `tests/test_profile.py`**
   - Add tests for expense display, ordering, user isolation, and empty state.
   - Run `./venv/bin/pytest` and verify 100% pass rate.

---

## 14. Relevant Existing Files and Proposed File Changes

| File | Status | Description of Proposed Changes |
| :--- | :--- | :--- |
| `@specs/profile-page-design.md` | Existing (Modified) | Updated specification incorporating the Recent Expenses requirement (category, description, date, amount, empty state, data model, and tests). |
| `@database/db.py` | Existing (Modify) | Ensure `expenses` table schema with foreign keys and indexes is defined in `init_db()`. |
| `@app.py` | Existing (Modify) | Query recent 5 expenses for the authenticated user and pass to `profile.html`. |
| `@templates/profile.html` | Existing (Modify) | Render Recent Expenses table (category, description, date, amount) and empty state. |
| `@static/css/style.css` | Existing (Modify) | Add styling for table, category badges, amounts, and empty states. |
| `tests/test_profile.py` | Existing (Modify) | Add test cases for recent expenses rendering, ordering, empty state, and user isolation. |

---

## 15. Dependencies, Risks, Assumptions, and Open Questions

### 15.1 Assumptions
- Expenses table follows the standard Spendly fields: `user_id`, `category`, `amount`, `date`, `description`.
- Currency is Indian Rupee (`₹`).
- A maximum limit of 5 recent transactions is displayed on the profile page to keep the profile overview concise.

### 15.2 Risks & Mitigations
- **Cross-User Data Leakage:** Ensure strict filtering by `WHERE user_id = ?` with `g.user["id"]`.
- **Table Missing Error:** Using `CREATE TABLE IF NOT EXISTS expenses` in `init_db()` guarantees the table exists before queries execute.
