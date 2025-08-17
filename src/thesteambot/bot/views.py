import discord

from thesteambot.bot.errors import AppCommandResponse


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
