import os
import tempfile
import pytest
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
