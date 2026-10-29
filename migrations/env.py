"""Alembic environment using the same PostgreSQL URL as the bot."""

import asyncio
import logging

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from giveaway_support_bot.config import load_database_url
from giveaway_support_bot.schema import metadata

logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")
database_url = make_url(load_database_url()).set(drivername="postgresql+asyncpg")


def run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_online() -> None:
    engine = create_async_engine(database_url, poolclass=pool.NullPool)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(run_migrations)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    context.configure(
        url=database_url,
        target_metadata=metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(run_online())
