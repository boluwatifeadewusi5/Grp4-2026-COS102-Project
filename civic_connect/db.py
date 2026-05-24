import os
from contextlib import contextmanager
import json
from pathlib import Path
from threading import RLock
from typing import Iterable, Optional

DATABASE_ENV = "CIVIC_CONNECT_DATABASE_URL"
LOCAL_DATABASE_ENV = "CIVIC_CONNECT_LOCAL_DATABASE_URL"
QUERY_TIMEOUT_ENV = "CIVIC_CONNECT_QUERY_TIMEOUT_MS"
DEFAULT_LOCAL_POSTGRES_URL = "postgresql://postgres:postgres@localhost:5432/civic_connect"

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT DEFAULT '',
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('casual','ngo','government')),
    organization_name TEXT DEFAULT '',
    location TEXT DEFAULT '',
    bio TEXT DEFAULT '',
    verified INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS friendships (
    id SERIAL PRIMARY KEY,
    requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK(status IN ('pending','accepted','rejected')) DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(requester_id, receiver_id)
);

CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    topic TEXT DEFAULT 'General',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS likes (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, post_id)
);

CREATE TABLE IF NOT EXISTS follows (
    id SERIAL PRIMARY KEY,
    follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(follower_id, following_id)
);

CREATE TABLE IF NOT EXISTS partner_requests (
    id SERIAL PRIMARY KEY,
    requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    note TEXT DEFAULT '',
    status TEXT NOT NULL CHECK(status IN ('pending','accepted','rejected')) DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(requester_id, receiver_id)
);

CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_a INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_b INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK(kind IN ('casual','org')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_a, user_b, kind)
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    attachment_name TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agreements (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    government_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ngo_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    budget DOUBLE PRECISION DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN ('draft','pending','changes_requested','approved','rejected','active','completed')) DEFAULT 'draft',
    created_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agreement_events (
    id SERIAL PRIMARY KEY,
    agreement_id INTEGER NOT NULL REFERENCES agreements(id) ON DELETE CASCADE,
    actor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    note TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    partner_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    focus_area TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'planning',
    progress INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    agreement_id INTEGER REFERENCES agreements(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    uploader_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    path TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at);
CREATE INDEX IF NOT EXISTS idx_posts_author_created ON posts(author_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_post_created ON comments(post_id, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_likes_post ON likes(post_id);
CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_follows_following ON follows(following_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_friendships_requester_status ON friendships(requester_id, status);
CREATE INDEX IF NOT EXISTS idx_friendships_receiver_status ON friendships(receiver_id, status);
CREATE INDEX IF NOT EXISTS idx_partner_requests_requester_status ON partner_requests(requester_id, status);
CREATE INDEX IF NOT EXISTS idx_partner_requests_receiver_status ON partner_requests(receiver_id, status);
CREATE INDEX IF NOT EXISTS idx_conversations_user_a ON conversations(user_a);
CREATE INDEX IF NOT EXISTS idx_conversations_user_b ON conversations(user_b);
CREATE INDEX IF NOT EXISTS idx_agreements_users ON agreements(government_id, ngo_id);
CREATE INDEX IF NOT EXISTS idx_projects_users ON projects(owner_id, partner_id);
CREATE INDEX IF NOT EXISTS idx_reports_project_created ON reports(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_users_role_name ON users(role, full_name);
CREATE INDEX IF NOT EXISTS idx_users_role_org ON users(role, organization_name);
"""

INSERT_ID_TABLES = {
    "users", "friendships", "posts", "comments", "follows", "partner_requests",
    "conversations", "messages", "agreements", "agreement_events",
    "documents", "projects", "reports", "notifications",
}

def get_config_database_url() -> Optional[str]:
    env_url = os.environ.get(DATABASE_ENV)
    if env_url:
        return env_url

    possible_paths = [
        Path("config.json"),
        Path(__file__).resolve().parent.parent / "config.json",
    ]

    for path in possible_paths:
        if path.exists():
            with open(path, "r", encoding="utf-8") as file:
                config = json.load(file)

            db_url = config.get(DATABASE_ENV) or config.get("CIVIC_CONNECT_DATABASE_URL")
            if db_url:
                return db_url

    return None

class Database:
    def __init__(self, url: Optional[str] = None):
        configured_url = (
            url
            or get_config_database_url()
            or os.environ.get(LOCAL_DATABASE_ENV)
        )

        self.url = configured_url or DEFAULT_LOCAL_POSTGRES_URL

        if self.url and "localhost" not in self.url and "127.0.0.1" not in self.url:
            self.mode = "hosted"
        else:
            self.mode = "local"

        self._conn = None
        self._lock = RLock()
        self.initialize()

    @contextmanager
    def connect(self):
        with self._lock:
            conn = self._connect()
            try:
                yield conn
                conn.commit()
            except Exception:
                if not conn.closed:
                    conn.rollback()
                raise

    def close(self):
        with self._lock:
            if self._conn is not None and not self._conn.closed:
                self._conn.close()
            self._conn = None

    def _connect(self):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "Civic Connect now uses Postgres only. "
                "Install dependencies with: python -m pip install -r requirements.txt"
            ) from exc

        if self._conn is not None and not self._conn.closed:
            return self._conn

        try:
            self._conn = psycopg.connect(self.url, row_factory=dict_row, connect_timeout=8)
            try:
                timeout_ms = int(os.environ.get(QUERY_TIMEOUT_ENV, "5000"))
            except ValueError:
                timeout_ms = 5000
            if timeout_ms > 0:
                timeout_ms = max(1000, min(timeout_ms, 60000))
                self._conn.execute(f"SET statement_timeout = {timeout_ms}")
            return self._conn
        except psycopg.OperationalError as exc:
            self._conn = None
            target = "hosted Postgres" if self.mode == "hosted" else "local Postgres"
            raise RuntimeError(
                f"Could not connect to {target}. Set {DATABASE_ENV} for online Postgres, "
                f"or start local Postgres and create a civic_connect database at "
                f"{DEFAULT_LOCAL_POSTGRES_URL}."
            ) from exc

    def _convert_sql(self, sql: str) -> str:
        return sql.replace("?", "%s")

    def _with_returning_id(self, sql: str) -> str:
        stripped = sql.strip()
        lower = stripped.lower()

        if not lower.startswith("insert into ") or " returning " in lower:
            return sql

        table = lower.removeprefix("insert into ").split("(", 1)[0].strip().strip('"')

        if table in INSERT_ID_TABLES:
            return f"{sql.rstrip()} RETURNING id"

        return sql

    def initialize(self):
        with self.connect() as conn:
            for statement in POSTGRES_SCHEMA.split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(statement)

    def execute(self, sql: str, params: Iterable = ()):
        with self.connect() as conn:
            cur = conn.execute(
                self._convert_sql(self._with_returning_id(sql)),
                tuple(params)
            )

            if cur.description:
                row = cur.fetchone()
                return row["id"] if row and "id" in row else None

            return None

    def query(self, sql: str, params: Iterable = ()):
        with self.connect() as conn:
            cur = conn.execute(self._convert_sql(sql), tuple(params))
            return [dict(r) for r in cur.fetchall()]

    def one(self, sql: str, params: Iterable = ()):
        with self.connect() as conn:
            cur = conn.execute(self._convert_sql(sql), tuple(params))
            row = cur.fetchone()
            return dict(row) if row else None
