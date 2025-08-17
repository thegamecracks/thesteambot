import datetime
import os

import discord
import hikari
from hikari.impl import RESTClientImpl

from thesteambot.bot.errors import DiscordOAuthError, MissingDiscordOAuthError
from thesteambot.db.client import DatabaseClient


async def acquire_rest_client(
    rest: hikari.RESTApp,
    db_client: DatabaseClient,
    user_id: int,
) -> RESTClientImpl:
    row = await db_client.get_discord_oauth(user_id)
    if row is None:
        raise MissingDiscordOAuthError(user_id)

    access_token, token_type = await maybe_refresh_access_token(
        rest,
        db_client,
        user_id,
        access_token=row["access_token"],
        token_type=row["token_type"],
        expires_at=row["expires_at"],
        refresh_token=row["refresh_token"],
        scope=row["scope"],
    )

    return rest.acquire(access_token, token_type)


async def maybe_refresh_access_token(
    rest: hikari.RESTApp,
    db_client: DatabaseClient,
    user_id: int,
    *,
    access_token: str,
    token_type: str,
    expires_at: datetime.datetime,
    refresh_token: str,
    scope: str,
) -> tuple[str, str]:
    now = discord.utils.utcnow()
    if (expires_at - now).total_seconds() > 60:
        return access_token, token_type

    return await refresh_access_token(
        rest,
        db_client,
        user_id,
        access_token=access_token,
        token_type=token_type,
        refresh_token=refresh_token,
        scope=scope,
    )


async def refresh_access_token(
    rest: hikari.RESTApp,
    db_client: DatabaseClient,
    user_id: int,
    *,
    access_token: str,
    token_type: str,
    refresh_token: str,
    scope: str,
) -> tuple[str, str]:
    client_id = int(os.environ["DISCORD_CLIENT_ID"])
    client_secret = os.environ["DISCORD_CLIENT_SECRET"]
    async with rest.acquire(access_token, token_type) as client:
        try:
            token = await client.refresh_access_token(
                client_id,
                client_secret,
                refresh_token,
            )
        except hikari.HTTPError as e:
            await db_client.delete_discord_oauth(user_id)
            message = "Failed to refresh access token for user"
            raise DiscordOAuthError(user_id, message) from e

    old_scopes = set(scope.split())
    new_scopes = set(str(s) for s in token.scopes)
    missing_scopes = old_scopes - new_scopes
    if missing_scopes:
        missing = ", ".join(sorted(new_scopes))
        message = f"Missing scopes in refreshed token: {missing}"
        await db_client.delete_discord_oauth(user_id)
        raise DiscordOAuthError(user_id, message)

    await db_client.set_discord_oauth(
        user_id,
        access_token=token.access_token,
        token_type=str(token.token_type),
        expires_in=token.expires_in,
        # HACK: hikari hints refresh_token as int
        refresh_token=str(token.refresh_token),
        scope=" ".join(sorted(new_scopes)),
    )
    return token.access_token, str(token.token_type)
