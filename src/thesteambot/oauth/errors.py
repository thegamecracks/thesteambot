class DiscordOAuthError(Exception):
    """Raised when the bot cannot retrieve a valid OAuth token for the given user."""

    def __init__(self, user_id: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user_id = user_id


class MissingDiscordOAuthError(DiscordOAuthError):
    """Raised when the user has not authenticated themselves with OAuth."""

    def __init__(self, user_id: int) -> None:
        super().__init__(user_id, "No authorization found for user")


class ExpiredDiscordOAuthError(DiscordOAuthError):
    """Raised when the user's authentication has expired."""

    def __init__(self, user_id: int) -> None:
        super().__init__(user_id, "Authorization expired for user")
