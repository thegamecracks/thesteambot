import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import discord
import hikari

from thesteambot.bot.bot import Bot
from thesteambot.db import create_pool

DEFAULT_EXTENSIONS = (
    "thesteambot.bot.cogs.cleanup",
    "thesteambot.bot.cogs.errors",
    "thesteambot.bot.cogs.oauth",
    "jishaku",
)


def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass


async def async_main() -> None:
    debug = os.getenv("DEBUG") not in (None, "", "0")
    extensions = os.getenv("BOT_EXTENSIONS")
    if extensions:
        extensions = extensions.split(",")
    else:
        extensions = DEFAULT_EXTENSIONS

    base_url = "https://{}".format(os.environ["DOMAIN"])
    token = os.environ["BOT_TOKEN"]

    discord.utils.setup_logging(root=True)

    async with create_pool() as pool, start_rest_app() as rest:
        bot = Bot(
            base_url=base_url,
            debug=debug,
            extensions=extensions,
            pool=pool,
            rest=rest,
        )
        await bot.start(token)


@asynccontextmanager
async def start_rest_app() -> AsyncIterator[hikari.RESTApp]:
    rest = hikari.RESTApp()
    await rest.start()
    try:
        yield rest
    finally:
        await rest.close()


if __name__ == "__main__":
    main()
