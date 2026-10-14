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


def test_register_get_renders_form(client):
    response = client.get("/register")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Create your account" in html
    assert 'name="name"' in html
    assert 'name="email"' in html
    assert 'name="password"' in html
    assert "Create account" in html


def test_register_success(client):
    response = client.post(
        "/register",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "securepassword123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Account created successfully! Please sign in." in html

    # Verify user saved in database
    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", ("jane@example.com",)).fetchone()
        assert user is not None
        assert user["name"] == "Jane Doe"
        assert user["email"] == "jane@example.com"
        assert user["password_hash"] != "securepassword123"
        assert check_password_hash(user["password_hash"], "securepassword123")


def test_register_duplicate_email(client):
    # First registration
    client.post(
        "/register",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "securepassword123",
        },
    )

    # Attempt second registration with same email
    response = client.post(
        "/register",
        data={
            "name": "Another Jane",
            "email": "jane@example.com",
            "password": "differentpassword123",
        },
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "An account with this email address already exists." in html
    assert 'value="Another Jane"' in html
    assert 'value="jane@example.com"' in html


def test_register_case_insensitive_email(client):
    # Register with lowercase
    client.post(
        "/register",
        data={
            "name": "Alex Smith",
            "email": "alex@example.com",
            "password": "password123",
        },
    )

    # Attempt with uppercase/mixed case
    response = client.post(
        "/register",
        data={
            "name": "Alex Smith",
            "email": "ALEX@EXAMPLE.COM",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "An account with this email address already exists." in html


def test_register_short_password(client):
    response = client.post(
        "/register",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "short",
        },
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Password must be at least 8 characters long." in html
    assert 'value="Jane Doe"' in html
    assert 'value="jane@example.com"' in html


def test_register_empty_name(client):
    response = client.post(
        "/register",
        data={
            "name": "   ",
            "email": "jane@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Please provide your full name." in html
    assert 'value="jane@example.com"' in html


def test_register_invalid_email(client):
    response = client.post(
        "/register",
        data={
            "name": "Jane Doe",
            "email": "not-an-email",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Please provide a valid email address." in html
    assert 'value="Jane Doe"' in html


# ------------------------------------------------------------------ #
# Login Tests                                                        #
# ------------------------------------------------------------------ #

def test_login_get_renders_form(client):
    response = client.get("/login")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Welcome back" in html
    assert 'name="email"' in html
    assert 'name="password"' in html
    assert "Sign in" in html


def test_login_empty_fields(client):
    response = client.post("/login", data={"email": "", "password": ""})
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Please provide both email and password." in html


def test_login_nonexistent_email(client):
    response = client.post(
        "/login",
        data={"email": "nobody@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Invalid email or password." in html
    assert 'value="nobody@example.com"' in html


def test_login_wrong_password(client):
    # Register user first
    client.post(
        "/register",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "correctpassword123",
        },
    )

    response = client.post(
        "/login",
        data={"email": "jane@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Invalid email or password." in html
    assert 'value="jane@example.com"' in html


def test_login_success(client):
    # Register user
    client.post(
        "/register",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "correctpassword123",
        },
    )

    response = client.post(
        "/login",
        data={"email": "jane@example.com", "password": "correctpassword123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Welcome back, Jane Doe!" in html
    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None
        assert sess.get("user_name") == "Jane Doe"


def test_login_case_insensitive_email(client):
    # Register in lowercase
    client.post(
        "/register",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "correctpassword123",
        },
    )

    # Login with uppercase email
    response = client.post(
        "/login",
        data={"email": "JANE@EXAMPLE.COM", "password": "correctpassword123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None


def test_login_redirect_when_already_authenticated(client):
    # Register and login
    client.post(
        "/register",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "correctpassword123",
        },
    )
    client.post(
        "/login",
        data={"email": "jane@example.com", "password": "correctpassword123"},
    )
    # Attempt visiting login page while logged in
    response = client.get("/login")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_register_redirect_when_already_authenticated(client):
    # Register and login
    client.post(
        "/register",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "correctpassword123",
        },
    )
    client.post(
        "/login",
        data={"email": "jane@example.com", "password": "correctpassword123"},
    )
    # Attempt visiting register page while logged in
    response = client.get("/register")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_login_next_url_redirect(client):
    client.post(
        "/register",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "correctpassword123",
        },
    )
    response = client.post(
        "/login?next=/profile",
        data={"email": "jane@example.com", "password": "correctpassword123"},
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/profile"


def test_login_next_url_open_redirect_prevented(client):
    client.post(
        "/register",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "correctpassword123",
        },
    )
    # Malicious next URL should fall back to landing
    response = client.post(
        "/login?next=https://evil.com",
        data={"email": "jane@example.com", "password": "correctpassword123"},
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


# ------------------------------------------------------------------ #
# Logout Tests                                                       #
# ------------------------------------------------------------------ #

def test_logout(client):
    client.post(
        "/register",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "correctpassword123",
        },
    )
    client.post(
        "/login",
        data={"email": "jane@example.com", "password": "correctpassword123"},
    )
    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None

    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "You have been signed out." in html
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None


# ------------------------------------------------------------------ #
# Access Control (@login_required) Tests                             #
# ------------------------------------------------------------------ #

def test_login_required_unauthenticated(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert "next=/profile" in response.headers["Location"]


def test_login_required_authenticated(client):
    client.post(
        "/register",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "correctpassword123",
        },
    )
    client.post(
        "/login",
        data={"email": "jane@example.com", "password": "correctpassword123"},
    )
    response = client.get("/profile")
    assert response.status_code == 200
    assert "Profile page — coming in Step 4" in response.data.decode("utf-8")


# ------------------------------------------------------------------ #
# Navigation State Tests                                             #
# ------------------------------------------------------------------ #

def test_navbar_links_state(client):
    # Unauthenticated state
    response = client.get("/")
    html = response.data.decode("utf-8")
    assert "Sign in" in html
    assert "Get started" in html
    assert "Sign out" not in html

    # Authenticate user
    client.post(
        "/register",
        data={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "correctpassword123",
        },
    )
    client.post(
        "/login",
        data={"email": "jane@example.com", "password": "correctpassword123"},
    )
    response = client.get("/")
    html = response.data.decode("utf-8")
    assert "Sign out" in html
    assert "Profile" in html
    assert "Sign in" not in html

