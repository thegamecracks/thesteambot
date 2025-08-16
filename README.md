# thesteambot

An experimental Discord application for fetching Steam connections from users.

This is mostly a learning exercise for myself as I try to combine a webserver,
OAuth2, and a Discord bot in the same project, so please don't use this in production!

## Requirements

- Discord application in https://discord.com/developers/applications
- Members privileged intent associated with your application's bot
- A reverse proxy, like Apache or Nginx, configured with your domain and TLS encryption

## Setup

Before running this application, you must follow these steps to set it up:

1. Copy and rename each of the `env.example` files to remove the `.example` suffix
   and add a `.` prefix, for example, `env.bot.example` becomes `.env.bot`.
2. Fill out each environment file with the appropriate values, such as your bot token
   and domain.

## Usage

To run all services at once:

```sh
docker compose up --build
```

To run a single service at a time:

```sh
docker compose up --build bot
docker compose up --build web
```

To run all services and live-rebuild when modifying source code:

```sh
docker compose up --build --remove-orphans --watch
```

Once running, the HTTP webserver can be accessed at port 2500.
