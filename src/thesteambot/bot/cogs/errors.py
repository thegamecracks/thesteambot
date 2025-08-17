import functools
import discord
from discord import app_commands
from discord.ext import commands

from thesteambot.bot.bot import Bot, Context
from thesteambot.bot.errors import CommandResponse, DiscordOAuthError
from thesteambot.bot.views import DiscordAuthorizeView


async def on_command_error(ctx: Context, error: commands.CommandError) -> None:
    original = getattr(error, "original", error)

    # Invalid commands
    if isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.DisabledCommand):
        pass
    # User input
    elif isinstance(error, commands.ConversionError):
        await ctx.reply("I could not parse your input.")
        if ctx.bot.debug:
            raise error
    elif isinstance(error, commands.UserInputError):
        await ctx.reply(f"Could not parse your input: {error}")
    # Checks
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.reply("This command must be used in a server.")
    elif isinstance(error, commands.NotOwner):
        pass
    elif isinstance(error, commands.MissingPermissions):
        perms = error.missing_permissions
        await ctx.reply(f"You must have the following permissions: {perms}")
    elif isinstance(error, commands.BotMissingPermissions):
        perms = error.missing_permissions
        await ctx.reply(f"I am missing the following permissions: {perms}")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"This command is on cooldown for {error.retry_after:.1f}s.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.reply("A check failed to pass before running this command.")
        if ctx.bot.debug:
            raise error
    # Runtime errors
    elif isinstance(error, CommandResponse):
        if message := str(error):
            await ctx.reply(message)
    elif isinstance(original, DiscordOAuthError):
        await ctx.reply(
            "You must authorize us with Discord to use this command! "
            "Click the button below and authorize us first, and then "
            "re-run the command.",
            delete_after=60,
            view=DiscordAuthorizeView(ctx.bot),
        )
        if ctx.bot.debug:
            raise error
    else:
        await ctx.reply("An unknown error occurred while running this command.")
        raise error


async def on_app_command_error(
    interaction: discord.Interaction[Bot],
    error: app_commands.AppCommandError,
) -> None:
    send = functools.partial(interaction_send, interaction)
    original = getattr(error, "original", error)

    # Invalid commands
    if isinstance(
        error,
        (
            app_commands.CommandNotFound,
            app_commands.CommandSignatureMismatch,
        ),
    ):
        await send("I do not recognize this command anymore. Sorry!")
        raise error
    # User input
    elif isinstance(error, app_commands.TransformerError):
        await send("I could not parse your input.")
        if interaction.client.debug:
            raise error
    # Checks
    elif isinstance(error, app_commands.NoPrivateMessage):
        await send("This command must be used in a server.")
    elif isinstance(error, app_commands.MissingPermissions):
        perms = error.missing_permissions
        await send(f"You must have the following permissions: {perms}")
    elif isinstance(error, app_commands.BotMissingPermissions):
        perms = error.missing_permissions
        await send(f"I am missing the following permissions: {perms}")
    elif isinstance(error, app_commands.CommandOnCooldown):
        await send(f"This command is on cooldown for {error.retry_after:.1f}s.")
    elif isinstance(error, app_commands.CheckFailure):
        await send("A check failed to pass before running this command.")
        if interaction.client.debug:
            raise error
    # Runtime errors
    elif isinstance(error, CommandResponse):
        if message := str(error):
            await send(message)
    elif isinstance(original, DiscordOAuthError):
        await send(
            "You must authorize us with Discord to use this command! "
            "Click the button below and authorize us first, and then "
            "re-run the command.",
            ephemeral=True,
            view=DiscordAuthorizeView(interaction.client),
        )
        if interaction.client.debug:
            raise error
    else:
        await send("An unknown error occurred while running this command.")
        raise error


async def interaction_send(interaction: discord.Interaction, *args, **kwargs) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(*args, **kwargs)
    else:
        kwargs.setdefault("ephemeral", True)
        await interaction.response.send_message(*args, **kwargs)


class Errors(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.setup_events()

    async def cog_unload(self) -> None:
        self.teardown_events()

    def setup_events(self) -> None:
        self._old_command_error = self.bot.on_command_error
        self.bot.on_command_error = on_command_error  # type: ignore

        self._old_tree_error = self.bot.tree.on_error
        self.bot.tree.error(on_app_command_error)

    def teardown_events(self) -> None:
        self.bot.on_command_error = self._old_command_error
        self.bot.tree.error(self._old_tree_error)


async def setup(bot: Bot):
    await bot.add_cog(Errors(bot))
