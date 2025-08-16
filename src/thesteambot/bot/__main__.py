import os

from thesteambot.bot.bot import Bot


def main() -> None:
    extensions = os.environ["BOT_EXTENSIONS"].split(",")
    token = os.environ["BOT_TOKEN"]

    bot = Bot(extensions=extensions)
    bot.run(token, root_logger=True)


if __name__ == "__main__":
    main()
