# Spendly — AI Agent Guidelines

This document provides permanent project instructions for AI coding agents working on the **Spendly** codebase. Follow these rules strictly to ensure safe, consistent, and minimal changes.

---

## Project Overview

- **Project Name:** Spendly
- **Purpose:** Personal expense tracking and budgeting application designed for logging expenses, spotting spending patterns, and managing budgets without spreadsheet complexity.
- **Tech Stack:**
  - **Backend:** Python 3.12, Flask 3.1.3, Werkzeug 3.1.6
  - **Database:** SQLite (managed via `@database/db.py`)
  - **Frontend:** Jinja2 templates, Vanilla CSS3 (custom design system), Vanilla JavaScript (ES6+)
  - **Typography:** DM Serif Display (headings/display) and DM Sans (body) via Google Fonts
  - **Testing:** pytest 8.3.5, pytest-flask 1.3.0 (`./venv/bin/pytest`)
  - **Development Server:** Flask app running on port 5001 with debug mode enabled (`python app.py`)
- **Repository Structure:**
  - `@app.py`: Flask application entry point, route definitions, and server configuration.
  - `@database/`: Database management package.
    - `@database/__init__.py`: Package initializer.
    - `@database/db.py`: SQLite connection handler (`get_db`), schema initialization (`init_db`), and seeding (`seed_db`).
  - `@templates/`: Jinja2 HTML templates.
    - `@templates/base.html`: Base layout shell (navigation, footer, global accessible modals for Terms & Privacy).
    - `@templates/landing.html`: Product landing page featuring hero section, metrics preview, and video walkthrough modal.
    - `@templates/login.html`: User login interface.
    - `@templates/register.html`: User registration interface.
  - `@static/`: Static assets directory.
    - `@static/css/style.css`: Unified stylesheet containing design tokens, reset, typography, responsive rules, and UI component styling.
    - `@static/js/main.js`: Client-side JavaScript handling accessible modal management, focus trapping, and YouTube embed lifecycles.
  - `@requirements.txt`: Python package requirements.
  - `@venv/`: Local Python virtual environment.

---

## File Modification Guidelines

- **File Locations:**
  - **Templates:** `@templates/` (`.html` Jinja2 templates extending `@templates/base.html`).
  - **Stylesheets:** `@static/css/style.css`.
  - **JavaScript:** `@static/js/main.js`.
  - **Backend Logic & Routing:** `@app.py`.
  - **Database Schemas & Queries:** `@database/db.py`.
  - **Dependencies:** `@requirements.txt`.
- **Pre-modification Inspection:** Always inspect existing code implementations and patterns before editing or adding code.
- **File Referencing:** Always mention exact filenames using `@filename` notation (e.g., `@templates/landing.html`, `@static/css/style.css`, `@app.py`) in task summaries and proposals.
- **Modify vs Create:**
  - Prefer modifying existing files over creating new files.
  - Only create new files when strictly necessary and architecturally appropriate.
- **No Guessing:** Never guess file paths, directory structures, or variable names; verify them against the repository.

---

## Coding Rules

- **Conventions & Architecture:** Adhere to established project patterns and file responsibilities.
- **Separation of Concerns:** Keep HTML (`@templates/`), CSS (`@static/css/style.css`), and JavaScript (`@static/js/main.js`) strictly separate.
- **No Inline CSS:** Do not use `style="..."` attributes in HTML templates. Add classes to `@static/css/style.css`.
- **CSS Sizing & Units:** Use `rem` units for font sizes, spacing, padding, and margins where appropriate, consistent with existing styling.
- **Design Token Reuse:** Reuse existing CSS variables defined in `:root` of `@static/css/style.css`:
  - Colors: `--ink`, `--ink-soft`, `--ink-muted`, `--ink-faint`, `--paper`, `--paper-warm`, `--paper-card`, `--accent`, `--accent-light`, `--accent-2`, `--accent-2-light`, `--danger`, `--danger-light`, `--border`, `--border-soft`.
  - Fonts: `--font-display`, `--font-body`.
  - Layout & Radii: `--max-width`, `--auth-width`, `--radius-sm`, `--radius-md`, `--radius-lg`.
- **Keep It Simple:** Avoid unnecessary dependencies, extra abstractions, code duplication, and overengineering. Keep changes minimal and focused.

---

## Change Scope

- **Minimal Footprint:** Edit only the files strictly required to accomplish the user's requested task.
- **No Unrelated Refactoring:** Do not clean up, reformat, or refactor code outside the immediate scope of the task.
- **Preserve Core Architecture:** Do not modify backend logic, database schemas, authentication, or API behavior unless explicitly requested.
- **Preserve Routes:** Maintain all existing Flask routes and navigation paths.
- **Respect User Work:** Never overwrite or revert existing user modifications.
- **No Duplication:** Do not create duplicate components, helper functions, or stylesheets.

---

## UI and Design Guidelines

- **Design System:** Strictly adhere to Spendly's visual identity (editorial warm paper aesthetic, serif display titles, clean sans body, forest green accent).
- **Responsiveness:** Maintain full responsiveness across desktop, tablet, and mobile breakpoints (notably at `768px` and `480px`).
- **Accessibility & Semantic HTML:**
  - Use semantic elements (`<main>`, `<section>`, `<nav>`, `<header>`, `<footer>`, `<button>`).
  - Maintain accessible ARIA attributes (`role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-controls`, `aria-haspopup`).
  - Preserve keyboard accessibility and focus management in interactive components like modals.
- **Reference Images:** When reference images are provided, match the visual specifications, proportions, and hierarchy closely.
- **Scoped Edits:** Do not redesign or alter sections unrelated to the assigned task.

---

## Testing and Verification

- **Tooling:** Check existing tools before running test commands. Pytest is available in the virtual environment via `./venv/bin/pytest`.
- **Execution:** Run relevant tests, linters, or manual verification steps when practical.
- **Visual & Functional Verification:** Confirm that interactive behaviors work and responsiveness remains intact.
- **Honest Reporting:** Never state or assume that a test passed without running it. Explicitly report if tests could not be run or if test suites are empty.

---

## Git Safety

- **No Destructive Commands:** Never run destructive Git commands (e.g., `git reset --hard`, `git push --force`, `git clean -fd`) without explicit user permission.
- **No Unauthorized Git Actions:** Do not commit, amend, rebase, reset, checkout branches, or push unless specifically directed by the user.
- **Preserve Unrelated Changes:** Never discard or overwrite existing uncommitted changes in the workspace.
- **Respect Verification Hooks:** Do not bypass pre-commit hooks or verification checks.

---

## Final Response Format

When completing any task, provide a concise summary using the following structure:

1. **What changed:** Clear, bulleted summary of modifications implemented.
2. **Exact files modified:** Listed with `@filename` notation (e.g., `@templates/base.html`, `@static/css/style.css`).
3. **Tests and verification performed:** Commands executed and their exact outcomes.
4. **Any issues or remaining work:** Any blockers, unrun tests, or pending items.
