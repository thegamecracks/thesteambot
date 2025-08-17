from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from thesteambot.bot.errors import AppCommandResponse

if TYPE_CHECKING:
    from thesteambot.bot.bot import Bot


class View(discord.ui.View):
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


class DiscordAuthorizeView(View):
    def __init__(self, bot: Bot):
        super().__init__()
        self.add_item(
            discord.ui.Button(
                label="Authorize",
                url=bot.url_for("/login/discord"),
            )
        )
