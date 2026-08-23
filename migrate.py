"""Schema migration bootstrap, run once at startup."""

import asyncio
import os

from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from db import database_url

HERE = os.path.dirname(os.path.abspath(__file__))


def _config() -> Config:
    cfg = Config(os.path.join(HERE, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(HERE, "alembic"))
    return cfg


async def _table_names() -> set[str]:
    engine = create_async_engine(database_url())
    try:
        async with engine.connect() as conn:
            return set(
                await conn.run_sync(lambda sync: inspect(sync).get_table_names())
            )
    finally:
        await engine.dispose()


def run_migrations() -> None:
    """Bring the database up to the latest revision.

    A database created by the pre-Alembic version of the app already has the
    tables but no version stamp; stamp it as the initial revision so the
    migration that would re-create those tables is skipped.
    """
    tables = asyncio.run(_table_names())

    cfg = _config()
    if "entries" in tables and "alembic_version" not in tables:
        command.stamp(cfg, "0001")
    command.upgrade(cfg, "head")
