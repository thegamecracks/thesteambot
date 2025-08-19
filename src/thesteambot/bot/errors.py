import discord
from discord import app_commands
from discord.ext import commands


class CommandResponse(commands.CommandError):
    """An exception containing a message to be shown directly to the command user."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AppCommandResponse(app_commands.AppCommandError):
    """An exception containing a message to be shown directly to the interaction user."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class MissingSteamUserError(Exception):
    """Raised when the bot cannot retrieve any Steam accounts for the given user."""

    def __init__(self, user: discord.User | discord.Member, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = user
