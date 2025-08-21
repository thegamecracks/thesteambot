import discord
from discord import app_commands
from discord.ext import commands

from thesteambot.bot.bot import Bot
from thesteambot.bot.views import (
    DiscordAuthorizeView,
    DiscordDeauthorizeView,
    create_manage_steam_user_view,
)
from thesteambot.oauth import DiscordOAuthError


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
            async with self.bot.acquire_rest_client(interaction.user) as client:
                await client.fetch_my_user()
        except DiscordOAuthError:
            connected = False
        else:
            connected = True

        if connected:
            view = DiscordDeauthorizeView(
                self.bot,
                interaction.user.id,
                "Your Discord account is already connected!\n"
                "\n"
                "If you'd like to disconnect your account, you may click the button below, "
                "or remove us from the Authorized Apps page in your Discord settings.\n"
                "Doing this will not remove any of your linked Steam accounts.",
            )
        else:
            view = DiscordAuthorizeView(
                self.bot,
                "Click the button below to connect your Discord account using OAuth.\n"
                "\n"
                "This command is usually unnecessary, as we will automatically prompt you "
                "to connect your account before performing any action that requires it.",
            )

        await interaction.response.send_message(ephemeral=True, view=view)
        view.set_last_interaction(interaction)

    @app_commands.command(
        name="steam",
        description="Connect your Steam accounts.",
    )
    @app_commands.checks.cooldown(1, 10, key=lambda interaction: interaction.user.id)
    async def steam(self, interaction: discord.Interaction[Bot]) -> None:
        view = await create_manage_steam_user_view(interaction)
        await interaction.response.send_message(ephemeral=True, view=view)
        view.set_last_interaction(interaction)


async def setup(bot: Bot) -> None:
    await bot.add_cog(OAuth(bot))
