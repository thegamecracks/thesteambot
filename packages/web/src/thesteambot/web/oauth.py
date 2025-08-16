from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

config = Config()
oauth = OAuth()
oauth.register(
    "discord",
    client_id=config("DISCORD_CLIENT_ID"),
    client_secret=config("DISCORD_CLIENT_SECRET"),
    access_token_url="https://discord.com/api/oauth2/token",
    authorize_url="https://discord.com/oauth2/authorize",
    api_base_url="https://discord.com/api/v10",
)
