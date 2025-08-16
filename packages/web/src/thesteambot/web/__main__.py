from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route


def homepage(request: Request) -> Response:
    return PlainTextResponse("Hello world!")


app = Starlette(
    routes=[
        Route("/", homepage),
    ],
)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0")


if __name__ == "__main__":
    main()
