import importlib.resources

from starlette.applications import Starlette
from starlette.config import Config
from starlette.datastructures import Secret
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

config = Config()
DEBUG = config("DEBUG") not in ("", "0")
DOMAIN = config("DOMAIN")
WEB_SECRET_KEY = config("WEB_SECRET_KEY", cast=Secret)

assert __package__ is not None
package = importlib.resources.files(__package__)

templates = Jinja2Templates(directory=str(package.joinpath("templates")))


def homepage(request: Request) -> Response:
    return templates.TemplateResponse(request, "index.j2")


allowed_hosts = [DOMAIN]
if DEBUG:
    allowed_hosts.extend(("localhost", "127.0.0.1"))

app = Starlette(
    debug=DEBUG,
    routes=[
        Route("/", homepage),
        Mount(
            "/static",
            name="static",
            app=StaticFiles(directory=str(package.joinpath("static"))),
        ),
    ],
    middleware=[
        Middleware(CORSMiddleware),
        Middleware(SessionMiddleware, secret_key=WEB_SECRET_KEY, https_only=True),
        Middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts,
            www_redirect=False,
        ),
    ],
)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0")


if __name__ == "__main__":
    main()
