import discord
from discord.ext import commands


class Bot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(
            command_prefix="xkcd",
            intents=intents,
        )
