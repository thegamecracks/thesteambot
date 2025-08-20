from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from thesteambot.bot.errors import AppCommandResponse

if TYPE_CHECKING:
    from thesteambot.bot.bot import Bot


class View(discord.ui.LayoutView):
    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        if not isinstance(error, AppCommandResponse):
            return await super().on_error(interaction, error, item)

        message = str(error)
        if not message:
            return

        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


class CancellableView(discord.ui.LayoutView):
    last_interaction: discord.Interaction | None = None

    def set_last_interaction(self, interaction: discord.Interaction) -> None:
        self.last_interaction = interaction

    async def delete(self) -> None:
        self.stop()
        interaction = self.last_interaction
        if interaction is not None and not interaction.is_expired():
            await interaction.delete_original_response()

    async def on_timeout(self) -> None:
        interaction = self.last_interaction
        if interaction is not None and not interaction.is_expired():
            await interaction.delete_original_response()


class DiscordAuthorizeActionRow(discord.ui.ActionRow):
    def __init__(self, bot: Bot):
        super().__init__()
        self.add_item(
            discord.ui.Button(
                label="Authorize",
                url=bot.url_for("/login/discord"),
            )
        )


def create_authorize_view(bot: Bot, content: str) -> discord.ui.LayoutView:
    container = discord.ui.Container(
        discord.ui.TextDisplay(content),
        discord.ui.Separator(),
        DiscordAuthorizeActionRow(bot),
    )
    view = discord.ui.LayoutView()
    view.add_item(container)
    return view
