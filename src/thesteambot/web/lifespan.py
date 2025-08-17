from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, cast

import asyncpg
import hikari
from starlette.applications import Starlette
from starlette.requests import Request

from thesteambot.db import create_pool


class State:
    hikari_rest: hikari.RESTApp
    pool: asyncpg.Pool


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[dict[str, Any]]:
    hikari_rest = hikari.RESTApp()
    await hikari_rest.start()

    async with create_pool() as pool:
        yield {
            "hikari_rest": hikari_rest,
            "pool": pool,
        }

    await hikari_rest.close()


def cast_state(request: Request) -> State:
    return cast(State, request.state)
