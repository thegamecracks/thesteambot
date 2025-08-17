import logging
from typing import Sequence

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class Bot(commands.Bot):
    def __init__(self, *, extensions: Sequence[str]) -> None:
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
        )

        self._extensions_to_load = extensions

    async def setup_hook(self) -> None:
        for extension in self._extensions_to_load:
            log.info(f"Loading extension {extension}")
            await self.load_extension(extension)
