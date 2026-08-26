"""Database layer: engine, session factory and ORM models.

The app supports SQLite, PostgreSQL and MariaDB/MySQL. Pick one with the
``DB_URL`` env var, e.g.::

    DB_URL=sqlite:///infabula.db
    DB_URL=postgresql://user:pass@host/infabula
    DB_URL=mysql://user:pass@host/infabula

Sync-style URLs are rewritten to their async driver automatically. The legacy
``DB_PATH`` var still works and maps to a SQLite file.
"""

import os
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# sync scheme -> async driver
ASYNC_DRIVERS = {
    "sqlite": "sqlite+aiosqlite",
    "postgresql": "postgresql+asyncpg",
    "postgres": "postgresql+asyncpg",
    "mysql": "mysql+aiomysql",
    "mariadb": "mysql+aiomysql",
}


def normalize_url(url: str) -> str:
    """Rewrite a plain URL to use this app's async driver for that backend."""
    scheme, sep, rest = url.partition("://")
    if not sep:
        return url
    if "+" in scheme:  # already names a driver, leave it alone
        return url
    return f"{ASYNC_DRIVERS.get(scheme, scheme)}://{rest}"


def sync_url(url: str) -> str:
    """Strip the async driver again — Alembic runs its own sync engine."""
    scheme, sep, rest = url.partition("://")
    if not sep:
        return url
    return f"{scheme.partition('+')[0]}://{rest}"


def database_url() -> str:
    url = os.getenv("DB_URL")
    if url:
        return normalize_url(url)
    return f"sqlite+aiosqlite:///{os.getenv('DB_PATH', 'infabula.db')}"


def is_sqlite(url: str | None = None) -> bool:
    return (url or database_url()).startswith("sqlite")


def sqlite_file(url: str | None = None) -> str | None:
    """Filesystem path behind a SQLite URL, or None for other backends.

    SQLite URLs carry one separator slash before a relative path and two
    before an absolute one, so exactly one slash is removed — stripping all
    of them would silently turn '/app/data/x.db' into 'app/data/x.db'.
    """
    url = url or database_url()
    if not is_sqlite(url):
        return None
    path = url.partition("://")[2]
    if path.startswith("/"):
        path = path[1:]
    return path or None


class Base(DeclarativeBase):
    pass


# Rows the app falls back to until users and babies are actually wired up.
DEFAULT_USER_ID = 1
DEFAULT_BABY_ID = 1

# Access levels a user can hold on a baby's log.
ROLE_OWNER = "owner"
ROLE_EDITOR = "editor"
ROLE_VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    username: Mapped[str | None] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    totp_secret: Mapped[str | None] = mapped_column(String(64))
    totp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[str | None] = mapped_column(
        String(32),
        default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    )
    last_login_at: Mapped[str | None] = mapped_column(String(32))


class WebauthnCredential(Base):
    """A registered passkey for a user. One user may have several."""

    __tablename__ = "webauthn_credentials"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    credential_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    sign_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    name: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[str | None] = mapped_column(
        String(32),
        default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    )


class UserSession(Base):
    """A logged-in session, keyed by the random token stored in the session cookie."""

    __tablename__ = "sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[str | None] = mapped_column(
        String(32),
        default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    )
    expires_at: Mapped[str] = mapped_column(String(32), nullable=False)


class ApiToken(Base):
    """A personal access token for scripted access to the API.

    Only the sha256 hash is stored — the raw token is shown once, at
    creation, the same way a password would be. ``prefix`` is the
    first few characters of the raw token, kept in the clear so a
    listed token can be told apart from the others without exposing
    enough of it to be useful on its own.
    """

    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[str | None] = mapped_column(
        String(32),
        default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    )
    last_used_at: Mapped[str | None] = mapped_column(String(32))


class Baby(Base):
    __tablename__ = "babies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    birthday: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[str | None] = mapped_column(
        String(32),
        default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    )


class BabyAccess(Base):
    """Which users may see or edit a given baby's log, and at what level."""

    __tablename__ = "baby_access"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    baby_id: Mapped[int] = mapped_column(
        ForeignKey("babies.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False, default=ROLE_OWNER)
    created_at: Mapped[str | None] = mapped_column(
        String(32),
        default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    )

    @property
    def can_edit(self) -> bool:
        return self.role in (ROLE_OWNER, ROLE_EDITOR)


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    baby_id: Mapped[int] = mapped_column(
        ForeignKey("babies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        default=DEFAULT_BABY_ID,
    )
    # Who logged it. Nullable: entries predating users have no known author.
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    # Timestamps stay as 'YYYY-MM-DDTHH:MM' local-time strings: the app is a
    # single-household journal where wall-clock time is what matters.
    ts_start: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    ts_end: Mapped[str | None] = mapped_column(String(32))
    note: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSON)
    ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[str | None] = mapped_column(
        String(32),
        default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    )

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "baby_id": self.baby_id,
            "user_id": self.user_id,
            "type": self.type,
            "ts_start": self.ts_start,
            "ts_end": self.ts_end,
            "note": self.note,
            "meta": self.meta or {},
            "ip": self.ip,
            "created_at": self.created_at,
        }


class IpName(Base):
    __tablename__ = "ip_names"

    ip: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


engine = create_async_engine(database_url(), future=True)
Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
