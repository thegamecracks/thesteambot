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


class DiscordOAuthError(Exception):
    """Raised when the bot cannot retrieve a valid OAuth token for the given user."""

    def __init__(self, user_id: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user_id = user_id


class MissingDiscordOAuthError(DiscordOAuthError):
    """Raised when the user has not authenticated themselves with OAuth."""

    def __init__(self, user_id: int) -> None:
        super().__init__(user_id, "No authorization found for user")
