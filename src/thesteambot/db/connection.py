import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

import asyncpg


def _is_dockerized() -> bool:
    return Path("/.dockerenv").exists()


def _get_connect_kwargs(
    *,
    host: str | None = None,
    port: int | None = None,
    user: str | None = None,
    password: str | None = None,
    database: str | None = None,
) -> dict[str, Any]:
    host = host or "db" if _is_dockerized() else "localhost"
    user = user or os.environ["DB_USER"]
    password = password or os.environ["DB_PASSWORD"]
    database = database or os.environ["DB_DATABASE"]
    port = port or int(os.environ["DB_PORT"])

    return {
        "host": host,
        "user": user,
        "password": password,
        "database": database,
        "port": port,
    }


@asynccontextmanager
async def connect(
    *,
    host: str | None = None,
    port: int | None = None,
    user: str | None = None,
    password: str | None = None,
    database: str | None = None,
) -> AsyncIterator[asyncpg.Connection]:
    connect_kwargs = _get_connect_kwargs(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
    )
    conn = await asyncpg.connect(**connect_kwargs)
    try:
        yield conn
    finally:
        await conn.close()


@asynccontextmanager
async def create_pool(
    *,
    host: str | None = None,
    port: int | None = None,
    user: str | None = None,
    password: str | None = None,
    database: str | None = None,
) -> AsyncIterator[asyncpg.Pool]:
    connect_kwargs = _get_connect_kwargs(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
    )
    async with asyncpg.create_pool(**connect_kwargs) as pool:
        yield pool
