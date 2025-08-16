from starlette.applications import Starlette
from starlette.config import Config
from starlette.datastructures import Secret
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

config = Config()
DOMAIN = config("DOMAIN")
WEB_SECRET_KEY = config("WEB_SECRET_KEY", cast=Secret)


def homepage(request: Request) -> Response:
    return PlainTextResponse("Hello world!")


app = Starlette(
    routes=[
        Route("/", homepage),
    ],
    middleware=[
        Middleware(CORSMiddleware),
        Middleware(SessionMiddleware, secret_key=WEB_SECRET_KEY, https_only=True),
        Middleware(
            TrustedHostMiddleware,
            allowed_hosts=[
                DOMAIN,
                "localhost",
                "127.0.0.1",
            ],
            www_redirect=False,
        ),
    ],
)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0")


if __name__ == "__main__":
    main()
