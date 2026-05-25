import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Optional

APP_DIR = Path.home() / ".civic_connect_tkinter"
APP_DIR.mkdir(exist_ok=True)
DEFAULT_DB_PATH = APP_DIR / "civic_connect.sqlite3"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT DEFAULT '',
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('casual','ngo','government')),
    organization_name TEXT DEFAULT '',
    location TEXT DEFAULT '',
    bio TEXT DEFAULT '',
    verified INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS friendships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requester_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending','accepted','rejected')) DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(requester_id, receiver_id),
    FOREIGN KEY(requester_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(receiver_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL,
    body TEXT NOT NULL,
    topic TEXT DEFAULT 'General',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(author_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY(author_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS likes (
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, post_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS partner_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requester_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    note TEXT DEFAULT '',
    status TEXT NOT NULL CHECK(status IN ('pending','accepted','rejected')) DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(requester_id, receiver_id),
    FOREIGN KEY(requester_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(receiver_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_a INTEGER NOT NULL,
    user_b INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('casual','org')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_a, user_b, kind),
    FOREIGN KEY(user_a) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(user_b) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    body TEXT NOT NULL,
    attachment_name TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY(sender_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agreements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    government_id INTEGER NOT NULL,
    ngo_id INTEGER NOT NULL,
    summary TEXT NOT NULL,
    budget REAL DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN ('draft','pending','changes_requested','approved','rejected','active','completed')) DEFAULT 'draft',
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(government_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(ngo_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agreement_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agreement_id INTEGER NOT NULL,
    actor_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    note TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agreement_id) REFERENCES agreements(id) ON DELETE CASCADE,
    FOREIGN KEY(actor_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agreement_id INTEGER,
    project_id INTEGER,
    uploader_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    path TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agreement_id) REFERENCES agreements(id) ON DELETE CASCADE,
    FOREIGN KEY(uploader_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    partner_id INTEGER,
    focus_area TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'planning',
    progress INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(partner_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(author_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

class Database:
    def __init__(self, path: Optional[str] = None):
        self.path = str(path or os.environ.get("CIVIC_CONNECT_DB", DEFAULT_DB_PATH))
        self.initialize()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self):
        with sqlite3.connect(self.path) as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    def execute(self, sql: str, params: Iterable = ()): 
        with self.connect() as conn:
            cur = conn.execute(sql, tuple(params))
            return cur.lastrowid

    def query(self, sql: str, params: Iterable = ()): 
        with self.connect() as conn:
            cur = conn.execute(sql, tuple(params))
            return [dict(r) for r in cur.fetchall()]

    def one(self, sql: str, params: Iterable = ()): 
        with self.connect() as conn:
            cur = conn.execute(sql, tuple(params))
            row = cur.fetchone()
            return dict(row) if row else None
