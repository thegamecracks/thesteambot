# thesteambot

## Requirements

- Discord application in https://discord.com/developers/applications
- Members privileged intent associated with your application's bot

## Usage

To run all services at once:

```sh
docker compose up --build
```

To run a single service at a time:

```sh
docker compose run --build --service-ports bot
docker compose run --build --service-ports web
```

To run all services and live-rebuild images when modifying source code:

```sh
docker compose watch
```

Once running, the HTTP webserver can be accessed at port 2500.
