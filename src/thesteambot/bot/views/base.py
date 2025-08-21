import discord

from thesteambot.bot.errors import AppCommandResponse


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
        if not interaction.response.is_done():
            raise RuntimeError(
                "Cannot set last interaction without responding "
                "to the interaction first"
            )

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
