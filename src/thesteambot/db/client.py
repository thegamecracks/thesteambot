import datetime
from typing import Sequence

from thesteambot.db.protocols import Connection, Record


class DatabaseClient:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    async def add_discord_user(self, user_id: int) -> None:
        await self.conn.execute(
            "INSERT INTO discord_user (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
            user_id,
        )

    async def add_discord_guild(self, guild_id: int) -> None:
        await self.conn.execute(
            "INSERT INTO discord_guild (guild_id) VALUES ($1) ON CONFLICT DO NOTHING",
            guild_id,
        )

    async def add_discord_channel(
        self, channel_id: int, *, guild_id: int | None
    ) -> None:
        await self.conn.execute(
            "INSERT INTO discord_channel (channel_id, guild_id) VALUES ($1, $2) "
            "ON CONFLICT DO NOTHING",
            channel_id,
            guild_id,
        )

    async def add_discord_member(self, *, guild_id: int, user_id: int) -> None:
        await self.conn.execute(
            "INSERT INTO discord_member (guild_id, user_id) VALUES ($1, $2) "
            "ON CONFLICT DO NOTHING",
            guild_id,
            user_id,
        )

    async def add_steam_user(self, user_id: int) -> None:
        # Intentionally don't suppress conflicts, since this is normally
        # an explicit step users have to do
        await self.conn.execute(
            "INSERT INTO steam_user (user_id) VALUES ($1)",
            user_id,
        )

    async def delete_steam_user(self, user_id: int) -> None:
        await self.conn.execute("DELETE FROM steam_user WHERE user_id = $1", user_id)

    async def add_discord_user_steam(self, user_id: int, *, steam_id: int) -> None:
        # Intentionally don't suppress conflicts, since this is normally
        # an explicit step users have to do
        await self.conn.execute(
            "INSERT INTO discord_user_steam (user_id, steam_id) VALUES ($1, $2)",
            user_id,
            steam_id,
        )

    async def get_discord_user_steam(self, user_id: int) -> Sequence[Record]:
        return await self.conn.fetch(
            "SELECT * FROM discord_user_steam WHERE user_id = $1",
            user_id,
        )

    async def get_one_discord_user_steam(
        self,
        *,
        user_id: int,
        steam_id: int,
    ) -> Record | None:
        return await self.conn.fetchrow(
            "SELECT * FROM discord_user_steam WHERE user_id = $1 AND steam_id = $2",
            user_id,
            steam_id,
        )

    async def add_discord_member_steam(
        self,
        *,
        guild_id: int,
        user_id: int,
        steam_id: int,
    ) -> None:
        # Intentionally don't suppress conflicts, since this is normally
        # an explicit step users have to do
        await self.conn.execute(
            "INSERT INTO discord_member_steam (guild_id, user_id, steam_id) "
            "VALUES ($1, $2, $3)",
            guild_id,
            user_id,
            steam_id,
        )

    async def get_discord_member_steam(
        self,
        *,
        guild_id: int,
        user_id: int,
    ) -> Sequence[Record]:
        return await self.conn.fetch(
            "SELECT * FROM discord_member_steam WHERE guild_id = $1 AND user_id = $2",
            guild_id,
            user_id,
        )

    async def get_one_discord_member_steam(
        self,
        *,
        guild_id: int,
        user_id: int,
        steam_id: int,
    ) -> Record | None:
        return await self.conn.fetchrow(
            "SELECT * FROM discord_member_steam WHERE guild_id = $1 AND user_id = $2 AND steam_id = $3",
            guild_id,
            user_id,
            steam_id,
        )

    async def delete_discord_member_steam(
        self,
        *,
        guild_id: int,
        user_id: int,
        steam_id: int,
    ) -> None:
        await self.conn.execute(
            "DELETE FROM discord_member_steam "
            "WHERE guild_id = $1 AND user_id = $2 AND steam_id = $3",
            guild_id,
            user_id,
            steam_id,
        )

    async def get_discord_oauth(self, user_id: int) -> Record | None:
        return await self.conn.fetchrow(
            "SELECT * FROM discord_oauth WHERE user_id = $1",
            user_id,
        )

    async def set_discord_oauth(
        self,
        user_id: int,
        *,
        access_token: str,
        token_type: str,
        expires_in: float | datetime.timedelta,
        refresh_token: str,
        scope: str,
    ) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        if not isinstance(expires_in, datetime.timedelta):
            expires_in = datetime.timedelta(seconds=expires_in)
        expires_at = now + expires_in

        await self.add_discord_user(user_id)
        await self.conn.execute(
            "INSERT INTO discord_oauth "
            "(user_id, access_token, token_type, expires_at, refresh_token, scope) "
            "VALUES ($1, $2, $3, $4, $5, $6) "
            "ON CONFLICT (user_id) DO UPDATE SET "
            "access_token = EXCLUDED.access_token, "
            "token_type = EXCLUDED.token_type, "
            "expires_at = EXCLUDED.expires_at, "
            "refresh_token = EXCLUDED.refresh_token, "
            "scope = EXCLUDED.scope",
            user_id,
            access_token,
            token_type,
            expires_at,
            refresh_token,
            scope,
        )

    async def delete_discord_oauth(self, user_id: int) -> None:
        await self.conn.execute(
            "DELETE FROM discord_oauth WHERE user_id = $1",
            user_id,
        )
