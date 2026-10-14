import os
import re
import sqlite3
from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from database.db import close_db, get_db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "spendly-dev-secret-key-change-in-production")
app.teardown_appcontext(close_db)

with app.app_context():
    init_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
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


@app.route("/login")
def login():
    return render_template("login.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


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
