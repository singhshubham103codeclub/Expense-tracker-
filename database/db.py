import os
import sqlite3
from flask import current_app, g

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spendly.db")


def get_db():
    """Returns a SQLite connection with row_factory and foreign keys enabled."""
    if "db" not in g:
        db_path = current_app.config.get("DATABASE", DEFAULT_DB_PATH) if current_app else DEFAULT_DB_PATH
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db


def close_db(e=None):
    """Closes the active database connection if open."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Creates all required tables if they do not exist."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (email);
    """)
    db.commit()


def seed_db():
    """Inserts sample data for development."""
    pass
