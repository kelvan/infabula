"""One-off: copy an existing SQLite database into a fresh PostgreSQL one.

Run the Alembic migrations against the target first so the schema exists,
then this fills it. Rows are copied through the ORM rather than as raw
SQL so SQLAlchemy converts the types that differ between the two
backends — SQLite keeps booleans as 0/1 and JSON as text, PostgreSQL
wants real booleans and json.

    uv run --extra postgres python sqlite_to_postgres.py \
        sqlite:///data/infabula.db postgresql://user:pass@host/infabula

Refuses to run if the target already holds data, so a re-run can't
silently double up the journal. Migration 0002 seeds a placeholder user
and baby, so a freshly migrated target is never actually empty — pass
--replace to clear the target first, which is what you want when the
source is meant to become the whole of it.
"""

import asyncio
import sys

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select, text
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from db import (
    ApiToken,
    Baby,
    BabyAccess,
    EmailVerification,
    Entry,
    User,
    UserSession,
    WebauthnCredential,
    normalize_url,
)

# Parents before children: every table's foreign keys must already resolve
# by the time its rows are inserted.
TABLES = [
    User,
    Baby,
    BabyAccess,
    Entry,
    UserSession,
    ApiToken,
    WebauthnCredential,
    EmailVerification,
]


async def copy(source_url: str, target_url: str, replace: bool = False) -> None:
    source_engine = create_async_engine(normalize_url(source_url))
    target_engine = create_async_engine(normalize_url(target_url))
    SourceSession = async_sessionmaker(source_engine, expire_on_commit=False)
    TargetSession = async_sessionmaker(target_engine, expire_on_commit=False)

    async with TargetSession() as target:
        for model in TABLES:
            existing = await target.scalar(
                select(func.count()).select_from(model)
            )
            if existing and not replace:
                raise SystemExit(
                    f"Target already has {existing} row(s) in "
                    f"{model.__tablename__}; refusing to copy into it. "
                    "Pass --replace to clear the target first."
                )

    if replace:
        async with TargetSession() as target:
            # Children first, so nothing is orphaned mid-delete.
            for model in reversed(TABLES):
                await target.execute(sa_delete(model))
            await target.commit()
        print("cleared target tables")

    for model in TABLES:
        async with SourceSession() as source:
            rows = (await source.scalars(select(model))).all()
            # Detach from the source session so the same values can be
            # re-added to the target as new rows.
            for row in rows:
                source.expunge(row)

        async with TargetSession() as target:
            for row in rows:
                await target.merge(row)
            await target.commit()
        print(f"{model.__tablename__:22} {len(rows):5} row(s)")

    await fix_sequences(target_engine)
    await source_engine.dispose()
    await target_engine.dispose()


async def fix_sequences(target_engine) -> None:
    """Point each identity sequence past the ids that were just inserted.

    Copied rows keep their original ids, which leaves PostgreSQL's
    sequences still at 1 — the next insert would collide with existing
    data. SQLite has no equivalent, so this has no counterpart in the
    source.
    """
    if target_engine.dialect.name != "postgresql":
        return

    async with target_engine.begin() as conn:
        for model in TABLES:
            table = model.__tablename__
            pks = list(sa_inspect(model).primary_key)
            # Composite keys (baby_access) and text keys (sessions.token)
            # have no sequence behind them.
            if len(pks) != 1 or pks[0].type.python_type is not int:
                continue
            name = pks[0].name
            # Identifiers can't be bound parameters, but these come from
            # our own model metadata, not from any input.
            await conn.execute(
                text(
                    f"SELECT setval("
                    f"  pg_get_serial_sequence('{table}', '{name}'),"
                    f"  COALESCE((SELECT MAX({name}) FROM {table}), 0) + 1,"
                    f"  false)"
                )
            )
            print(f"sequence reset: {table}.{name}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--replace"]
    if len(args) != 2:
        raise SystemExit(
            f"usage: {sys.argv[0]} [--replace] <source-url> <target-url>"
        )
    asyncio.run(copy(args[0], args[1], replace="--replace" in sys.argv))
