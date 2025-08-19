from typing import NamedTuple

import discord
from discord import app_commands
from discord.ext import commands

from thesteambot.bot.bot import Bot
from thesteambot.bot.errors import MissingSteamUserError
from thesteambot.bot.views import CancellableView, DiscordAuthorizeView
from thesteambot.db import DatabaseClient
from thesteambot.oauth import DiscordOAuthError


async def get_steam_ids(db_client: DatabaseClient, user_id: int):
    rows = await db_client.get_discord_user_steam(user_id)
    current_steam_ids: set[int] = {row["steam_id"] for row in rows}
    return current_steam_ids


class SteamConnection(NamedTuple):
    id: int
    name: str
    public: bool


class ManageSteamUserView(CancellableView):
    def __init__(
        self,
        bot: Bot,
        user_id: int,
        steam_ids: set[int],
        connections: dict[int, SteamConnection],
    ) -> None:
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.steam_ids = steam_ids
        self.connections = connections
        self.on_select.options = [
            discord.SelectOption(
                label=c.name if (c := connections.get(steam_id)) else str(steam_id),
                value=str(steam_id),
            )
            for steam_id in steam_ids
        ]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.select(options=[])
    async def on_select(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select,
    ) -> None:
        self.set_last_interaction(interaction)

        async with self.bot.acquire_db_client() as db_client:
            rows = await db_client.get_discord_user_steam(interaction.user.id)
            current = {row["steam_id"]: row for row in rows}

        selected = int(select.values[0])
        connection = self.connections.get(selected)
        if connection is not None:
            name = f"{connection.name} (ID {connection.id})"
        else:
            name = f"{selected}"

        if selected not in current:
            view = AddSteamUserView(self.bot, interaction.user.id, selected, name)
            view.set_last_interaction(interaction)
            await interaction.response.send_message(
                f"{name} has not yet been connected with us.\n"
                "Would you like to connect this Steam account? "
                "You can undo this afterwards by selecting the account again.\n"
                "\n"
                "Connecting will allow us to show your Steam account to other users, "
                "even if you have otherwise hidden the account on your profile.",
                ephemeral=True,
                view=view,
            )
        else:
            view = DeleteSteamUserView(self.bot, interaction.user.id, selected, name)
            view.set_last_interaction(interaction)
            created_at = discord.utils.format_dt(current[selected]["created_at"])
            await interaction.response.send_message(
                f"{name} has already been connected with us on {created_at}.\n"
                "Would you like to disconnect this Steam account? "
                "Beware that any data we have stored with this account will be "
                "deleted, including the list of servers you've connected this "
                "account to.",
                ephemeral=True,
                view=view,
            )


class AddSteamUserView(CancellableView):
    def __init__(self, bot: Bot, user_id: int, steam_id: int, steam_name: str):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.steam_id = steam_id
        self.steam_name = steam_name

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button(label="Connect", style=discord.ButtonStyle.primary)
    async def on_delete(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        async with self.bot.acquire_db_client() as db_client:
            await db_client.add_steam_user(self.steam_id)
            await db_client.add_discord_user_steam(
                interaction.user.id,
                steam_id=self.steam_id,
            )

        await interaction.response.edit_message(
            content=f"Successfully connected the Steam account, {self.steam_name}!",
            view=None,
        )
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def on_cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        self.set_last_interaction(interaction)
        await interaction.response.defer()
        await self.delete()


class DeleteSteamUserView(CancellableView):
    def __init__(self, bot: Bot, user_id: int, steam_id: int, steam_name: str):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.steam_id = steam_id
        self.steam_name = steam_name

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def on_delete(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        async with self.bot.acquire_db_client() as db_client:
            await db_client.delete_steam_user(self.steam_id)

        await interaction.response.edit_message(
            content=f"Successfully disconnected the Steam account, {self.steam_name}!",
            view=None,
        )
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def on_cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        self.set_last_interaction(interaction)
        await interaction.response.defer()
        await self.delete()


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

    @app_commands.command(
        name="steam",
        description="Connect your Steam accounts.",
    )
    @app_commands.checks.cooldown(1, 10, key=lambda interaction: interaction.user.id)
    async def steam(self, interaction: discord.Interaction) -> None:
        # TODO: support direct authentication with Steam
        async with self.bot.acquire_rest_client(interaction.user) as client:
            connections = await client.fetch_my_connections()

        connections = [c for c in connections if c.type == "steam"]
        connections = {
            int(c.id): SteamConnection(
                id=int(c.id),
                name=c.name,
                public=c.visibility == 1,
            )
            for c in connections
        }

        async with self.bot.acquire_db_client() as db_client:
            current_steam_ids = await get_steam_ids(db_client, interaction.user.id)

        if not connections and not current_steam_ids:
            raise MissingSteamUserError(interaction.user)

        view = ManageSteamUserView(
            self.bot,
            interaction.user.id,
            current_steam_ids | set(connections),
            connections,
        )
        view.set_last_interaction(interaction)
        await interaction.response.send_message(
            "Available Steam accounts:",
            ephemeral=True,
            view=view,
        )


async def setup(bot: Bot) -> None:
    await bot.add_cog(OAuth(bot))
