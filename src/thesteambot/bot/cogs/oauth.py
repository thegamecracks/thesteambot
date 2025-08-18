import discord
from discord import app_commands
from discord.ext import commands

from thesteambot.bot.bot import Bot
from thesteambot.bot.errors import DiscordOAuthError
from thesteambot.bot.views import DiscordAuthorizeView


class OAuth(
    commands.GroupCog,
    group_name="connect",
    group_description="Connect your accounts using OAuth.",
):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="discord",
        description="Connect your Discord account.",
    )
    @app_commands.checks.cooldown(1, 10, key=lambda interaction: interaction.user.id)
    async def discord_command(self, interaction: discord.Interaction) -> None:
        try:
            async with self.bot.acquire_rest_client(interaction.user):
                pass
        except DiscordOAuthError:
            connected = False
        else:
            connected = True

        if connected:
            await interaction.response.send_message(
                "Your Discord account is already connected!\n"
                "To disconnect your account, you may remove us from the Authorized Apps "
                "page in your Discord settings.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "Click the button below to connect your Discord account using OAuth.\n"
                "\n"
                "This command is usually unnecessary, as we will automatically prompt you "
                "to connect your account before performing any action that requires it.",
                ephemeral=True,
                view=DiscordAuthorizeView(self.bot),
            )


async def setup(bot: Bot) -> None:
    await bot.add_cog(OAuth(bot))
