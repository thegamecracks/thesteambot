CREATE TABLE discord_user (
    user_id BIGINT PRIMARY KEY
);

-- https://discord.com/developers/docs/topics/oauth2
CREATE TABLE discord_oauth (
    user_id BIGINT PRIMARY KEY REFERENCES discord_user (user_id),
    access_token TEXT NOT NULL,
    token_type TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    refresh_token TEXT NOT NULL,
    scope TEXT NOT NULL
);
