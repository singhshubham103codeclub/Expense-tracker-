import os
import tempfile
import pytest
from flask import g, session
from werkzeug.security import check_password_hash

from app import app
from database.db import get_db, init_db


@pytest.fixture
def client():
    # Setup temporary database for test isolation
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    app.config["TESTING"] = True
    app.config["DATABASE"] = db_path

    with app.app_context():
        init_db()

    with app.test_client() as client:
        yield client

    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)


def register_and_login(client, name="Jane Doe", email="jane@example.com", password="password123"):
    client.post(
        "/register",
        data={"name": name, "email": email, "password": password},
        follow_redirects=True,
    )
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def test_profile_unauthenticated_redirect(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert "next=/profile" in response.headers["Location"]

    followed = client.get("/profile", follow_redirects=True)
    assert followed.status_code == 200
    html = followed.data.decode("utf-8")
    assert "Please sign in to access this page." in html


def test_profile_authenticated_view(client):
    register_and_login(client, name="Jane Doe", email="jane@example.com")
    response = client.get("/profile")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert "JD" in html
    assert "Jane Doe" in html
    assert "jane@example.com" in html
    assert "Active Member" in html
    assert "Member since" in html
    assert "Personal Information" in html
    assert "Security &amp; Password" in html or "Security & Password" in html
    assert '<a href="/profile" target="_self"' in html


def test_profile_nav_link_same_tab(client):
    register_and_login(client, name="Jane Doe", email="jane@example.com")
    response = client.get("/")
    html = response.data.decode("utf-8")
    assert '<a href="/profile" target="_self"' in html
    # Ensure it does not open in a new tab
    assert 'target="_blank"' not in html.split('href="/profile"')[1].split('>')[0]


def test_profile_single_word_initials(client):
    register_and_login(client, name="Cher", email="cher@example.com")
    response = client.get("/profile")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "CH" in html
    assert "Cher" in html


def test_update_profile_success(client):
    register_and_login(client, name="Jane Doe", email="jane@example.com")

    response = client.post(
        "/profile",
        data={
            "action": "update_profile",
            "name": "Jane Smith",
            "email": "janesmith@example.com",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Your profile details have been updated." in html
    assert "Jane Smith" in html
    assert "janesmith@example.com" in html

    # Verify database update
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", ("janesmith@example.com",)).fetchone()
        assert user is not None
        assert user["name"] == "Jane Smith"

    # Verify session update
    with client.session_transaction() as sess:
        assert sess.get("user_name") == "Jane Smith"


def test_update_profile_keep_same_email(client):
    register_and_login(client, name="Jane Doe", email="jane@example.com")

    response = client.post(
        "/profile",
        data={
            "action": "update_profile",
            "name": "Jane Updated",
            "email": "jane@example.com",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Your profile details have been updated." in html
    assert "Jane Updated" in html

    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", ("jane@example.com",)).fetchone()
        assert user["name"] == "Jane Updated"


def test_update_profile_duplicate_email(client):
    # Register User A
    register_and_login(client, name="User A", email="usera@example.com")
    client.get("/logout")

    # Register User B and remain logged in
    register_and_login(client, name="User B", email="userb@example.com")

    # User B tries to change email to User A's email
    response = client.post(
        "/profile",
        data={
            "action": "update_profile",
            "name": "User B",
            "email": "usera@example.com",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "An account with this email address already exists." in html

    # Verify User B email unchanged in database
    with app.app_context():
        db = get_db()
        user_b = db.execute("SELECT * FROM users WHERE email = ?", ("userb@example.com",)).fetchone()
        assert user_b is not None
        assert user_b["name"] == "User B"


def test_update_profile_validation_errors(client):
    register_and_login(client, name="Jane Doe", email="jane@example.com")

    # Empty name
    response = client.post(
        "/profile",
        data={
            "action": "update_profile",
            "name": "",
            "email": "jane@example.com",
        },
        follow_redirects=True,
    )
    assert "Please provide your full name (2–100 characters)." in response.data.decode("utf-8")

    # Name too short
    response = client.post(
        "/profile",
        data={
            "action": "update_profile",
            "name": "J",
            "email": "jane@example.com",
        },
        follow_redirects=True,
    )
    assert "Please provide your full name (2–100 characters)." in response.data.decode("utf-8")

    # Invalid email
    response = client.post(
        "/profile",
        data={
            "action": "update_profile",
            "name": "Jane Doe",
            "email": "invalid-email-format",
        },
        follow_redirects=True,
    )
    assert "Please provide a valid email address." in response.data.decode("utf-8")


def test_change_password_success(client):
    register_and_login(client, name="Jane Doe", email="jane@example.com", password="oldpassword123")

    response = client.post(
        "/profile",
        data={
            "action": "change_password",
            "current_password": "oldpassword123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Password changed successfully." in html

    # Log out
    client.get("/logout")

    # Try logging in with old password -> should fail
    login_fail = client.post(
        "/login",
        data={"email": "jane@example.com", "password": "oldpassword123"},
        follow_redirects=True,
    )
    assert "Invalid email or password." in login_fail.data.decode("utf-8")

    # Try logging in with new password -> should succeed
    login_success = client.post(
        "/login",
        data={"email": "jane@example.com", "password": "newpassword123"},
        follow_redirects=True,
    )
    assert "Welcome back, Jane Doe!" in login_success.data.decode("utf-8")


def test_change_password_wrong_current(client):
    register_and_login(client, name="Jane Doe", email="jane@example.com", password="correctpassword123")

    response = client.post(
        "/profile",
        data={
            "action": "change_password",
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Current password is incorrect." in html


def test_change_password_mismatch(client):
    register_and_login(client, name="Jane Doe", email="jane@example.com", password="password123")

    response = client.post(
        "/profile",
        data={
            "action": "change_password",
            "current_password": "password123",
            "new_password": "newpassword123",
            "confirm_password": "mismatchpassword",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "New passwords do not match." in html


def test_change_password_too_short(client):
    register_and_login(client, name="Jane Doe", email="jane@example.com", password="password123")

    response = client.post(
        "/profile",
        data={
            "action": "change_password",
            "current_password": "password123",
            "new_password": "short",
            "confirm_password": "short",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "New password must be at least 8 characters long." in html


def test_change_password_same_as_current(client):
    register_and_login(client, name="Jane Doe", email="jane@example.com", password="password123")

    response = client.post(
        "/profile",
        data={
            "action": "change_password",
            "current_password": "password123",
            "new_password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "New password must be different from your current password." in html


def test_profile_recent_expenses_display(client):
    register_and_login(client, name="Jane Doe", email="jane@example.com")

    with app.app_context():
        db = get_db()
        user = db.execute("SELECT id FROM users WHERE email = ?", ("jane@example.com",)).fetchone()
        db.execute(
            """
            INSERT INTO expenses (user_id, category, amount, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user["id"], "Food", 250.0, "2026-10-14", "Lunch at cafe"),
        )
        db.execute(
            """
            INSERT INTO expenses (user_id, category, amount, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user["id"], "Travel", 350.0, "2026-10-13", "Metro recharge"),
        )
        db.execute(
            """
            INSERT INTO expenses (user_id, category, amount, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user["id"], "Bills", 1200.0, "2026-10-12", "Electricity bill"),
        )
        db.commit()

    response = client.get("/profile")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert "Recent Expenses" in html
    assert "Food" in html
    assert "Lunch at cafe" in html
    assert "14 Oct 2026" in html
    assert "₹250.00" in html

    assert "Travel" in html
    assert "Metro recharge" in html
    assert "13 Oct 2026" in html
    assert "₹350.00" in html

    assert "Bills" in html
    assert "Electricity bill" in html
    assert "12 Oct 2026" in html
    assert "₹1,200.00" in html
    assert "3 logged" in html


def test_profile_recent_expenses_limit_and_order(client):
    register_and_login(client, name="Jane Doe", email="jane@example.com")

    with app.app_context():
        db = get_db()
        user = db.execute("SELECT id FROM users WHERE email = ?", ("jane@example.com",)).fetchone()
        for i in range(1, 8):
            db.execute(
                """
                INSERT INTO expenses (user_id, category, amount, date, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user["id"], "Food", 100.0 * i, f"2026-10-0{i}", f"Expense Day {i}"),
            )
        db.commit()

    response = client.get("/profile")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Should contain top 5: Day 7, 6, 5, 4, 3
    assert "Expense Day 7" in html
    assert "Expense Day 6" in html
    assert "Expense Day 5" in html
    assert "Expense Day 4" in html
    assert "Expense Day 3" in html

    # Older days should not be in the recent 5 list
    assert "Expense Day 2" not in html
    assert "Expense Day 1" not in html

    # Day 7 must appear before Day 3 in the HTML
    pos7 = html.find("Expense Day 7")
    pos3 = html.find("Expense Day 3")
    assert pos7 < pos3

    assert "7 logged" in html


def test_profile_recent_expenses_tenant_isolation(client):
    # Register User A and create an expense
    register_and_login(client, name="User A", email="usera@example.com")
    with app.app_context():
        db = get_db()
        user_a = db.execute("SELECT id FROM users WHERE email = ?", ("usera@example.com",)).fetchone()
        db.execute(
            """
            INSERT INTO expenses (user_id, category, amount, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_a["id"], "Shopping", 999.0, "2026-10-14", "Confidential User A Purchase"),
        )
        db.commit()

    client.get("/logout")

    # Register User B and visit profile
    register_and_login(client, name="User B", email="userb@example.com")
    response = client.get("/profile")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert "Confidential User A Purchase" not in html
    assert "No expenses logged yet" in html


def test_profile_recent_expenses_empty_state(client):
    register_and_login(client, name="Jane Doe", email="jane@example.com")
    response = client.get("/profile")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert "Recent Expenses" in html
    assert "No expenses logged yet" in html
    assert "Log an expense" in html
    assert "0 logged" in html

