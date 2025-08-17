from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, cast

import asyncpg
from starlette.applications import Starlette
from starlette.requests import Request

from thesteambot.db.connection import create_pool


class State:
    pool: asyncpg.Pool


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[dict[str, Any]]:
    async with create_pool() as pool:
        yield {"pool": pool}


def cast_state(request: Request) -> State:
    return cast(State, request.state)
