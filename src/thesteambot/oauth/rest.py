from __future__ import annotations

import datetime
import os
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import AsyncIterator, Callable

import hikari
from hikari.impl import RESTClientImpl

from thesteambot.db import DatabaseClient
from thesteambot.oauth import (
    DiscordOAuthError,
    ExpiredDiscordOAuthError,
    MissingDiscordOAuthError,
)


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
    now = datetime.datetime.now(datetime.timezone.utc)
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
        except hikari.ClientHTTPResponseError as e:
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


@asynccontextmanager
async def wrap_rest_client(
    acquire_db_client: Callable[[], AbstractAsyncContextManager[DatabaseClient]],
    client: RESTClientImpl,
    user_id: int,
) -> AsyncIterator[RESTClientImpl]:
    async with client:
        try:
            yield client
        except hikari.UnauthorizedError as e:
            # FIXME: Improve Discord OAuth invalidation for 401 responses
            #
            # We don't have enough information in this error to know if it
            # was our client that threw the error, or a different client.
            # For example, if we entered two clients and the outer client
            # received 401, the inner-most client would be the first to hit
            # this try-except. As a result, we may end up invalidating someone
            # else's login even though they weren't the one that caused the 401.
            async with acquire_db_client() as db_client:
                await db_client.delete_discord_oauth(user_id)

            raise ExpiredDiscordOAuthError(user_id) from e
