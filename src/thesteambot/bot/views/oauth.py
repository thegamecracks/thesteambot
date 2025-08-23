from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, NamedTuple

import discord

from thesteambot.bot.bot import Bot
from thesteambot.bot.errors import MissingSteamUserError
from thesteambot.bot.views import CancellableView
from thesteambot.db import DatabaseClient
from thesteambot.oauth import revoke_access_token

if TYPE_CHECKING:
    from thesteambot.bot.bot import Bot


class DiscordAuthorizeView(CancellableView):
    def __init__(self, bot: Bot, content: str) -> None:
        self.display = discord.ui.TextDisplay(content)
        self.container = discord.ui.Container(
            self.display,
            discord.ui.Separator(),
            DiscordAuthorizeActionRow(bot),
        )
        self.add_item(self.container)


class DiscordAuthorizeActionRow(discord.ui.ActionRow):
    def __init__(self, bot: Bot):
        super().__init__()
        self.add_item(
            discord.ui.Button(
                label="Authorize",
                url=bot.url_for("/login/discord"),
            )
        )


class DiscordDeauthorizeView(CancellableView):
    def __init__(self, bot: Bot, user_id: int, content: str) -> None:
        super().__init__()
        self.bot = bot
        self.user_id = user_id

        self.display = discord.ui.TextDisplay(content)
        self.container = discord.ui.Container(
            self.display,
            discord.ui.Separator(),
            DiscordDeauthorizeActionRow(),
        )
        self.add_item(self.container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id


class DiscordDeauthorizeActionRow(discord.ui.ActionRow[DiscordDeauthorizeView]):
    @discord.ui.button(label="Disconnect", style=discord.ButtonStyle.danger)
    async def on_disconnect(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        assert self.view is not None

        async with self.view.bot.acquire_db_client() as client:
            await revoke_access_token(self.view.bot.rest, client, self.view.user_id)

        self.view.display.content = (
            "Successfully deauthorized us from your Discord account!"
        )
        self.on_disconnect.disabled = True
        self.on_cancel.disabled = True

        await interaction.response.edit_message(view=self.view)
        self.view.set_last_interaction(interaction)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def on_cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        assert self.view is not None
        await interaction.response.defer()
        self.view.set_last_interaction(interaction)
        await self.view.delete()


async def get_steam_ids(db_client: DatabaseClient, user_id: int):
    rows = await db_client.get_discord_user_steam(user_id)
    current_steam_ids: set[int] = {row["steam_id"] for row in rows}
    return current_steam_ids


class SteamConnection(NamedTuple):
    id: int
    name: str
    public: bool


class SteamViewState(NamedTuple):
    user_id: int
    steam_id: int
    name: str | None  # Externally retrieved from Discord connections

    user: SteamUserState | None
    member: SteamMemberState | None

    @property
    def display_name(self) -> str:
        if self.name is not None:
            return f"{self.name} (ID {self.steam_id})"
        return f"{self.steam_id}"


class SteamUserState(NamedTuple):
    created_at: datetime.datetime


class SteamMemberState(NamedTuple):
    guild_id: int
    created_at: datetime.datetime


async def get_steam_view_state(
    db_client: DatabaseClient,
    *,
    user_id: int,
    steam_id: int,
    name: str | None,
    guild_id: int | None,
) -> SteamViewState:
    user = await db_client.get_one_discord_user_steam(
        user_id=user_id,
        steam_id=steam_id,
    )
    if user is None:
        return SteamViewState(
            user_id=user_id,
            steam_id=steam_id,
            name=name,
            user=None,
            member=None,
        )

    member: SteamMemberState | None = None
    if guild_id is not None:
        member = await _get_steam_member_state(
            db_client,
            user_id,
            steam_id,
            guild_id,
        )

    return SteamViewState(
        user_id=user_id,
        steam_id=steam_id,
        name=name,
        user=SteamUserState(created_at=user["created_at"]),
        member=member,
    )


async def _get_steam_member_state(
    db_client: DatabaseClient,
    user_id: int,
    steam_id: int,
    guild_id: int,
) -> SteamMemberState | None:
    member = await db_client.get_one_discord_member_steam(
        guild_id=guild_id,
        user_id=user_id,
        steam_id=steam_id,
    )
    if member is None:
        return None

    return SteamMemberState(
        guild_id=guild_id,
        created_at=member["created_at"],
    )


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
            discord.ui.TextDisplay("# Link Steam Accounts"),
            discord.ui.ActionRow(select),
            discord.ui.Separator(spacing=discord.SeparatorSpacing.large),
        )
        self.add_item(container)
        return container

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    async def get_steam_view_state(
        self,
        db_client: DatabaseClient,
        *,
        user_id: int,
        steam_id: int,
        guild_id: int | None,
    ) -> SteamViewState:
        connection = self.connections.get(steam_id)
        name = connection.name if connection is not None else None
        return await get_steam_view_state(
            db_client,
            user_id=user_id,
            steam_id=steam_id,
            name=name,
            guild_id=guild_id,
        )


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

        user_id = interaction.user.id
        steam_id = int(self.values[0])
        guild_id = interaction.guild.id if interaction.guild is not None else None
        async with self.view.bot.acquire_db_client() as db_client:
            state = await self.view.get_steam_view_state(
                db_client,
                user_id=user_id,
                steam_id=steam_id,
                guild_id=guild_id,
            )

        self.show_user_actions(state)
        await interaction.response.edit_message(view=self.view)
        self.view.set_last_interaction(interaction)

    def show_user_actions(self, state: SteamViewState) -> None:
        assert self.view is not None
        container = self.view.reset_container()

        name = state.display_name
        if state.user is None:
            display = discord.ui.TextDisplay(
                f"{name} has not yet been connected with us.\n"
                "Would you like to connect this Steam account? "
                "You can undo this afterwards by selecting the account again.\n"
                "\n"
                "Connecting will allow us to show your Steam account to other users, "
                "even if you have otherwise hidden the account on your profile."
            )
        else:
            created_at = discord.utils.format_dt(state.user.created_at)
            display = discord.ui.TextDisplay(
                f"{name} has already been connected with us on {created_at}.\n"
                "Would you like to disconnect this Steam account? "
                "Beware that any data we have stored with this account will be "
                "deleted, including the list of servers you've connected this "
                "account to."
            )

        container.add_item(display)
        container.add_item(SteamUserActionRow(self.view.bot, state, display))


class SteamUserActionRow(discord.ui.ActionRow[ManageSteamUserView]):
    def __init__(
        self,
        bot: Bot,
        state: SteamViewState,
        display: discord.ui.TextDisplay,
    ):
        super().__init__()
        self.bot = bot
        self.state = state
        self.display = display

        if state.user is None:
            self.on_toggle.label = "Connect"
            self.on_toggle.style = discord.ButtonStyle.primary
        else:
            self.on_toggle.label = "Delete"
            self.on_toggle.style = discord.ButtonStyle.danger

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.state.user_id

    @discord.ui.button()
    async def on_toggle(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        assert self.view is not None

        name = self.state.display_name
        if self.state.user is None:
            await self.add_steam_user(interaction.user.id)
            self.display.content = f"Successfully connected the Steam account, {name}!"
            button.label = "Connected"
        else:
            await self.delete_steam_user()
            self.display.content = (
                f"Successfully disconnected the Steam account, {name}!"
            )
            button.label = "Deleted"

        button.disabled = True
        await interaction.response.edit_message(view=self.view)
        self.view.set_last_interaction(interaction)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def on_back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        assert self.view is not None
        self.view.reset_container()
        await interaction.response.edit_message(view=self.view)
        self.view.set_last_interaction(interaction)

    async def add_steam_user(self, user_id: int) -> None:
        steam_id = self.state.steam_id
        async with self.bot.acquire_db_client() as db_client:
            await db_client.add_steam_user(steam_id)
            await db_client.add_discord_user_steam(user_id, steam_id=steam_id)

    async def delete_steam_user(self) -> None:
        steam_id = self.state.steam_id
        async with self.bot.acquire_db_client() as db_client:
            await db_client.delete_steam_user(steam_id)


async def create_manage_steam_user_view(
    interaction: discord.Interaction[Bot],
) -> ManageSteamUserView:
    bot = interaction.client

    # TODO: support direct authentication with Steam
    async with bot.acquire_rest_client(interaction.user) as client:
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

    async with bot.acquire_db_client() as db_client:
        current_steam_ids = await get_steam_ids(db_client, interaction.user.id)

    if not connections and not current_steam_ids:
        raise MissingSteamUserError(interaction.user)

    return ManageSteamUserView(
        interaction.client,
        interaction.user.id,
        current_steam_ids | set(connections),
        connections,
    )
