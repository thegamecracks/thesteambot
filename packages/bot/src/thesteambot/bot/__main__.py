import os

from thesteambot.bot.bot import Bot


def main() -> None:
    token = os.environ["BOT_TOKEN"]

    bot = Bot()
    bot.run(token, root_logger=True)


if __name__ == "__main__":
    main()
