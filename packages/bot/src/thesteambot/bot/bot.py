import discord
from discord.ext import commands


class Bot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix="xkcd",
            intents=discord.Intents.default(),
        )
