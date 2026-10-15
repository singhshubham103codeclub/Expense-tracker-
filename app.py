from datetime import datetime
import functools
import os
import re
import sqlite3
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import close_db, get_db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "spendly-dev-secret-key-change-in-production")
app.teardown_appcontext(close_db)

with app.app_context():
    init_db()


@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if g.user is None:
            session.clear()


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please sign in to access this page.", "error")
            return redirect(url_for("login", next=request.path))
        return view(**kwargs)
    return wrapped_view


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("landing"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or len(name) < 2 or len(name) > 100:
            return render_template(
                "register.html",
                error="Please provide your full name.",
                name=name,
                email=email,
            )

        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not email or len(email) > 255 or not re.match(email_pattern, email):
            return render_template(
                "register.html",
                error="Please provide a valid email address.",
                name=name,
                email=email,
            )

        if not password or len(password) < 8 or len(password) > 128:
            return render_template(
                "register.html",
                error="Password must be at least 8 characters long.",
                name=name,
                email=email,
            )

        db = get_db()
        existing_user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing_user:
            return render_template(
                "register.html",
                error="An account with this email address already exists.",
                name=name,
                email=email,
            )

        try:
            db.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return render_template(
                "register.html",
                error="An account with this email address already exists.",
                name=name,
                email=email,
            )

        flash("Account created successfully! Please sign in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


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


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("landing"))


def get_user_initials(name):
    if not name:
        return "?"
    parts = name.strip().split()
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def format_member_since(created_at):
    if not created_at:
        return "Recently"
    try:
        if isinstance(created_at, datetime):
            return created_at.strftime("%B %Y")
        clean_str = str(created_at).split(".")[0]
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(clean_str, fmt)
                return dt.strftime("%B %Y")
            except ValueError:
                continue
        return str(created_at)[:10]
    except Exception:
        return "Recently"


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    db = get_db()

    if request.method == "POST":
        action = request.form.get("action", "")

        # --- Handle Profile Info Update ---
        if action == "update_profile":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()

            if not name or len(name) < 2 or len(name) > 100:
                flash("Please provide your full name (2–100 characters).", "error")
                return redirect(url_for("profile"))

            email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
            if not email or len(email) > 255 or not re.match(email_pattern, email):
                flash("Please provide a valid email address.", "error")
                return redirect(url_for("profile"))

            # Check if email is already taken by another user
            existing = db.execute(
                "SELECT id FROM users WHERE email = ? AND id != ?", (email, g.user["id"])
            ).fetchone()
            if existing:
                flash("An account with this email address already exists.", "error")
                return redirect(url_for("profile"))

            try:
                db.execute(
                    "UPDATE users SET name = ?, email = ? WHERE id = ?",
                    (name, email, g.user["id"]),
                )
                db.commit()
            except sqlite3.IntegrityError:
                flash("An account with this email address already exists.", "error")
                return redirect(url_for("profile"))

            session["user_name"] = name
            flash("Your profile details have been updated.", "success")
            return redirect(url_for("profile"))

        # --- Handle Password Change ---
        elif action == "change_password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not current_password or not new_password or not confirm_password:
                flash("All password fields are required.", "error")
                return redirect(url_for("profile"))

            user_auth = db.execute(
                "SELECT password_hash FROM users WHERE id = ?", (g.user["id"],)
            ).fetchone()

            if not user_auth or not check_password_hash(user_auth["password_hash"], current_password):
                flash("Current password is incorrect.", "error")
                return redirect(url_for("profile"))

            if len(new_password) < 8 or len(new_password) > 128:
                flash("New password must be at least 8 characters long.", "error")
                return redirect(url_for("profile"))

            if new_password != confirm_password:
                flash("New passwords do not match.", "error")
                return redirect(url_for("profile"))

            if check_password_hash(user_auth["password_hash"], new_password):
                flash("New password must be different from your current password.", "error")
                return redirect(url_for("profile"))

            db.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (generate_password_hash(new_password), g.user["id"]),
            )
            db.commit()
            flash("Password changed successfully.", "success")
            return redirect(url_for("profile"))

    # Fetch latest user data for GET or fall-through
    user = db.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ?", (g.user["id"],)
    ).fetchone()

    initials = get_user_initials(user["name"] if user else "")
    member_since = format_member_since(user["created_at"] if user else None)

    # Fetch recent 5 expenses for the current user
    expenses_rows = db.execute(
        """
        SELECT id, category, description, date, amount
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
        LIMIT 5
        """,
        (g.user["id"],),
    ).fetchall()

    recent_expenses = []
    for exp in expenses_rows:
        raw_date = exp["date"]
        formatted_date = str(raw_date)
        if raw_date:
            try:
                if isinstance(raw_date, datetime):
                    formatted_date = raw_date.strftime("%d %b %Y")
                else:
                    d_obj = datetime.strptime(str(raw_date).split()[0], "%Y-%m-%d")
                    formatted_date = d_obj.strftime("%d %b %Y")
            except Exception:
                formatted_date = str(raw_date)

        amount_val = float(exp["amount"]) if exp["amount"] is not None else 0.0
        formatted_amount = f"₹{amount_val:,.2f}"

        recent_expenses.append({
            "id": exp["id"],
            "category": exp["category"],
            "description": exp["description"],
            "formatted_date": formatted_date,
            "formatted_amount": formatted_amount,
            "amount": amount_val,
            "date": exp["date"],
        })

    # Count total transactions for user
    total_count_row = db.execute(
        "SELECT COUNT(*) as count FROM expenses WHERE user_id = ?",
        (g.user["id"],),
    ).fetchone()
    total_expenses_count = total_count_row["count"] if total_count_row else 0

    return render_template(
        "profile.html",
        user=user,
        initials=initials,
        member_since=member_since,
        recent_expenses=recent_expenses,
        total_expenses_count=total_expenses_count,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
