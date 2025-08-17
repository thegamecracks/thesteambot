import datetime
import asyncpg


class DatabaseClient:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn

    async def get_discord_oauth(self, user_id: int) -> asyncpg.Record | None:
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

        await self.conn.execute(
            "INSERT INTO discord_user (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
            user_id,
        )
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
