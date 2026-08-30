import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from db import Base, database_url, sync_url

config = context.config
if config.config_file_name is not None:
    # disable_existing_loggers defaults to True, which silently kills every
    # logger created before this runs — including the app's own and
    # uvicorn's, since migrations run at import time in the same process.
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata
url = database_url()


def run_migrations_offline() -> None:
    context.configure(
        url=sync_url(url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # batch mode lets ALTER-poor SQLite handle future column changes
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    # Reuse the app's async driver so each backend needs only one driver.
    engine = create_async_engine(url, poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
