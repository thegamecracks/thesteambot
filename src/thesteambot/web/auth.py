from authlib.integrations.base_client import OAuthError
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from thesteambot.db.client import DatabaseClient
from thesteambot.web.lifespan import cast_state
from thesteambot.web.oauth import oauth
from thesteambot.web.templating import templates


class DiscordAccessToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: float
    refresh_token: str
    scope: str


async def authorize_discord(request: Request) -> Response:
    page = "auth/discord.j2"
    context = {"success": False}

    discord = oauth.create_client("discord")
    assert discord is not None

    try:
        token = await discord.authorize_access_token(request)
        token = DiscordAccessToken.model_validate(token)
    except OAuthError:
        return templates.TemplateResponse(request, page, context=context)

    state = cast_state(request)
    client = state.hikari_rest.acquire(token.access_token, token.token_type)
    async with client:
        user = await client.fetch_my_user()

    async with state.pool.acquire() as conn:
        client = DatabaseClient(conn)
        await client.set_discord_oauth(
            user.id,
            access_token=token.access_token,
            token_type=token.token_type,
            expires_in=token.expires_in,
            refresh_token=token.refresh_token,
            scope=token.scope,
        )

    request.session["discord-user-id"] = user.id
    context["success"] = True
    return templates.TemplateResponse(request, page, context=context)


routes = [
    Route("/discord", authorize_discord),
]
