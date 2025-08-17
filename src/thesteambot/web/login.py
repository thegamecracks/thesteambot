from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route

from thesteambot.db import DatabaseClient
from thesteambot.web.lifespan import cast_state
from thesteambot.web.oauth import oauth


async def login_discord(request: Request) -> Response:
    async def authorize_redirect() -> Response:
        discord = oauth.create_client("discord")
        assert discord is not None

        redirect_uri = request.url_for("auth", path="/discord")
        scope = ("connections", "identify")

        return await discord.authorize_redirect(
            request,
            redirect_uri,
            scope=scope,
            prompt="none",
        )

    user_id = request.session.get("discord-user-id")
    if user_id is None:
        return await authorize_redirect()

    state = cast_state(request)
    async with state.pool.acquire() as conn:
        client = DatabaseClient(conn)
        row = await client.get_discord_oauth(user_id)

    if row is None:
        return await authorize_redirect()

    # FIXME: show page or toast indicating they're already authenticated
    return RedirectResponse(request.url_for("homepage"))


routes = [
    Route("/discord", login_discord),
]
