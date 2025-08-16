from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from thesteambot.web.oauth import oauth


async def login_discord(request: Request) -> Response:
    discord = oauth.create_client("discord")
    assert discord is not None

    # TODO: check if user is already authorized

    redirect_uri = request.url_for("auth", path="/discord")
    scopes = ("connections", "identify")

    return await discord.authorize_redirect(
        request,
        redirect_uri,
        scopes=" ".join(scopes),
        prompt="none",
    )


routes = [
    Route("/discord", login_discord),
]
