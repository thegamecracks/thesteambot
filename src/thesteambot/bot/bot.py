import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Sequence

import asyncpg
import discord
import hikari
from discord.ext import commands
from hikari.api import RESTClient

from thesteambot.bot.oauth import acquire_rest_client
from thesteambot.db import DatabaseClient

log = logging.getLogger(__name__)


class Bot(commands.Bot):
    def __init__(
        self,
        *,
        base_url: str,
        debug: bool,
        extensions: Sequence[str],
        pool: asyncpg.Pool,
        rest: hikari.RESTApp,
    ) -> None:
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
        )

        self.debug = debug
        self.pool = pool
        self.rest = rest
        self._base_url = base_url
        self._extensions_to_load = extensions

    async def setup_hook(self) -> None:
        for extension in self._extensions_to_load:
            log.info(f"Loading extension {extension}")
            await self.load_extension(extension)

    @asynccontextmanager
    async def acquire_rest_client(
        self,
        user: int | discord.User | discord.Member,
    ) -> AsyncIterator[RESTClient]:
        if isinstance(user, int):
            user_id = user
        else:
            user_id = user.id

        async with self.pool.acquire() as conn:
            db_client = DatabaseClient(conn)
            rest_client = await acquire_rest_client(self.rest, db_client, user_id)

        async with rest_client:
            yield rest_client

    def url_for(self, path: str) -> str:
        return self._base_url + "/" + path.lstrip("/")


class Context(commands.Context[Bot]): ...
