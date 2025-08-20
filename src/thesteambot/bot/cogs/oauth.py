import datetime
from typing import NamedTuple

import discord
from discord import app_commands
from discord.ext import commands

from thesteambot.bot.bot import Bot
from thesteambot.bot.errors import MissingSteamUserError
from thesteambot.bot.views import CancellableView, create_authorize_view
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
        self.reset_container()

    def reset_container(self) -> discord.ui.Container:
        self.clear_items()
        select = ManageSteamUserSelect(self.steam_ids, self.connections)
        container = discord.ui.Container(
            discord.ui.TextDisplay("Available Steam accounts:"),
            discord.ui.ActionRow(select),
            discord.ui.Separator(spacing=discord.SeparatorSpacing.large),
        )
        self.add_item(container)
        return container

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id


class ManageSteamUserSelect(discord.ui.Select[ManageSteamUserView]):
    def __init__(
        self,
        steam_ids: set[int],
        connections: dict[int, SteamConnection],
    ) -> None:
        super().__init__(
            options=[
                discord.SelectOption(
                    label=c.name if (c := connections.get(steam_id)) else str(steam_id),
                    value=str(steam_id),
                )
                for steam_id in steam_ids
            ],
            placeholder="Select a Steam account",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view is not None
        self.view.set_last_interaction(interaction)

        async with self.view.bot.acquire_db_client() as db_client:
            rows = await db_client.get_discord_user_steam(interaction.user.id)
            current = {row["steam_id"]: row for row in rows}

        selected = int(self.values[0])
        connection = self.view.connections.get(selected)
        if connection is not None:
            name = f"{connection.name} (ID {connection.id})"
        else:
            name = f"{selected}"

        row = current.get(selected)
        if row is not None:
            created_at = row["created_at"]
        else:
            created_at = None

        self.show_user_actions(interaction.user.id, selected, name, created_at)
        await interaction.response.edit_message(view=self.view)

    def show_user_actions(
        self,
        user_id: int,
        selected: int,
        name: str,
        created_at: datetime.datetime | None,
    ) -> None:
        assert self.view is not None
        container = self.view.reset_container()

        if created_at is None:
            display = discord.ui.TextDisplay(
                f"{name} has not yet been connected with us.\n"
                "Would you like to connect this Steam account? "
                "You can undo this afterwards by selecting the account again.\n"
                "\n"
                "Connecting will allow us to show your Steam account to other users, "
                "even if you have otherwise hidden the account on your profile."
            )
            is_connecting = True
        else:
            created_at_str = discord.utils.format_dt(created_at)
            display = discord.ui.TextDisplay(
                f"{name} has already been connected with us on {created_at_str}.\n"
                "Would you like to disconnect this Steam account? "
                "Beware that any data we have stored with this account will be "
                "deleted, including the list of servers you've connected this "
                "account to."
            )
            is_connecting = False

        container.add_item(display)
        container.add_item(
            SteamUserActionRow(
                self.view.bot,
                user_id,
                selected,
                name,
                display,
                is_connecting,
            )
        )


class SteamUserActionRow(discord.ui.ActionRow[ManageSteamUserView]):
    def __init__(
        self,
        bot: Bot,
        user_id: int,
        steam_id: int,
        steam_name: str,
        display: discord.ui.TextDisplay,
        is_connecting: bool,
    ):
        super().__init__()
        self.bot = bot
        self.user_id = user_id
        self.steam_id = steam_id
        self.steam_name = steam_name
        self.display = display
        self.is_connecting = is_connecting

        if is_connecting:
            self.on_toggle.label = "Connect"
            self.on_toggle.style = discord.ButtonStyle.primary
        else:
            self.on_toggle.label = "Delete"
            self.on_toggle.style = discord.ButtonStyle.danger

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button()
    async def on_toggle(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        assert self.view is not None
        self.view.set_last_interaction(interaction)

        if self.is_connecting:
            await self.add_steam_user(interaction.user.id)
            self.display.content = (
                f"Successfully connected the Steam account, {self.steam_name}!"
            )
            button.label = "Connected"
        else:
            await self.delete_steam_user()
            self.display.content = (
                f"Successfully disconnected the Steam account, {self.steam_name}!"
            )
            button.label = "Deleted"

        button.disabled = True
        await interaction.response.edit_message(view=self.view)
        # TODO: allow re-selecting same account

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def on_back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        assert self.view is not None
        self.view.set_last_interaction(interaction)
        self.view.reset_container()
        await interaction.response.edit_message(view=self.view)

    async def add_steam_user(self, user_id: int) -> None:
        async with self.bot.acquire_db_client() as db_client:
            await db_client.add_steam_user(self.steam_id)
            await db_client.add_discord_user_steam(user_id, steam_id=self.steam_id)

    async def delete_steam_user(self) -> None:
        async with self.bot.acquire_db_client() as db_client:
            await db_client.delete_steam_user(self.steam_id)


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
            view = create_authorize_view(
                self.bot,
                "Click the button below to connect your Discord account using OAuth.\n"
                "\n"
                "This command is usually unnecessary, as we will automatically prompt you "
                "to connect your account before performing any action that requires it.",
            )
            await interaction.response.send_message(ephemeral=True, view=view)

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
        await interaction.response.send_message(ephemeral=True, view=view)


async def setup(bot: Bot) -> None:
    await bot.add_cog(OAuth(bot))
