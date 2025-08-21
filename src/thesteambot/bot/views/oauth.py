from __future__ import annotations

from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from thesteambot.bot.bot import Bot


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
