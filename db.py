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
from datetime import datetime

from sqlalchemy import JSON, String, Text
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
    """Filesystem path behind a SQLite URL, or None for other backends."""
    url = url or database_url()
    if not is_sqlite(url):
        return None
    path = url.partition("://")[2].lstrip("/")
    return path or None


class Base(DeclarativeBase):
    pass


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    # Timestamps stay as 'YYYY-MM-DDTHH:MM' local-time strings: the app is a
    # single-household journal where wall-clock time is what matters.
    ts_start: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    ts_end: Mapped[str | None] = mapped_column(String(32))
    note: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSON)
    ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[str | None] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    def as_dict(self) -> dict:
        return {
            "id": self.id,
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
