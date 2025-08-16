from authlib.integrations.base_client import OAuthError
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from thesteambot.web.oauth import oauth
from thesteambot.web.templating import templates


async def authorize_discord(request: Request) -> Response:
    page = "auth/discord.j2"
    context = {"success": False}

    discord = oauth.create_client("discord")
    assert discord is not None

    try:
        token = await discord.authorize_access_token(request)
    except OAuthError:
        return templates.TemplateResponse(request, page, context=context)

    # TODO: store access token
    print(repr(token))

    context["success"] = True
    return templates.TemplateResponse(request, page, context=context)


routes = [
    Route("/discord", authorize_discord),
]
