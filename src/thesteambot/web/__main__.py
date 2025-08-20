from thesteambot.web.app import app


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0")


if __name__ == "__main__":
    main()
