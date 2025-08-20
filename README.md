# thesteambot

![](https://github.com/user-attachments/assets/46f1cf45-d5ec-4047-9d60-8089534507ee)

An experimental Discord application for fetching Steam connections from users.

This is mostly a learning exercise for myself as I try to combine a webserver,
OAuth2, and a Discord bot in the same project, so please don't use this in production!

## Setup

Before running this application, you must have the following prepared:

- [Docker Engine] installed on your system

- Your own Discord application from https://discord.com/developers/applications

  For the Discord bot to work, you must also have the Members privileged intent
  enabled in your Bot page.

- A reverse proxy, like [Apache] or [Nginx], configured with your domain and TLS encryption

  Anything able to forward port 2500 => 443 and encrypt your traffic will work.
  [ngrok]'s free tier is a suitable option for local testing.

  An example Nginx configuration can be found in [etc/nginx/sites-available/thesteambot].

[Docker Engine]: https://docs.docker.com/get-started/get-docker/
[Apache]: https://httpd.apache.org/
[Nginx]: https://nginx.org/
[ngrok]: https://ngrok.com/
[etc/nginx/sites-available/thesteambot]: /etc/nginx/sites-available/thesteambot

Once those are ready, you can configure the project:

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
