import asyncio
import os

import discord

from thesteambot.bot.bot import Bot
from thesteambot.db.connection import create_pool


def main() -> None:
    asyncio.run(async_main())


async def async_main() -> None:
    extensions = os.environ["BOT_EXTENSIONS"].split(",")
    token = os.environ["BOT_TOKEN"]

    discord.utils.setup_logging(root=True)

    async with create_pool() as pool:
        bot = Bot(extensions=extensions, pool=pool)
        await bot.start(token)


if __name__ == "__main__":
    main()
