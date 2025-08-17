CREATE TABLE discord_guild (guild_id BIGINT PRIMARY KEY);
CREATE TABLE discord_channel (
    channel_id BIGINT PRIMARY KEY,
    guild_id BIGINT
        REFERENCES discord_guild (guild_id)
        ON DELETE CASCADE
);
CREATE TABLE discord_member (
    guild_id BIGINT
        REFERENCES discord_guild (guild_id)
        ON DELETE CASCADE,
    user_id BIGINT
        REFERENCES discord_user (user_id)
        ON DELETE CASCADE,
    PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE steam_user (user_id BIGINT PRIMARY KEY);

-- Link Discord users to Steam users
CREATE TABLE discord_user_steam (
    user_id BIGINT
        REFERENCES discord_user (user_id)
        ON DELETE CASCADE,
    steam_id BIGINT
        UNIQUE
        REFERENCES steam_user (user_id)
        ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP(0),
    PRIMARY KEY (user_id, steam_id)
);

-- Link Steam users to Discord members, separate from Discord users
-- to control data visibility
CREATE TABLE discord_member_steam (
    guild_id BIGINT
        REFERENCES discord_guild (guild_id)
        ON DELETE CASCADE,
    user_id BIGINT
        REFERENCES discord_user (user_id)
        ON DELETE CASCADE,
    steam_id BIGINT
        REFERENCES steam_user (user_id)
        ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP(0),
    PRIMARY KEY (guild_id, user_id, steam_id),
    FOREIGN KEY (guild_id, user_id) REFERENCES discord_member (guild_id, user_id)
        ON DELETE CASCADE,
    FOREIGN KEY (user_id, steam_id) REFERENCES discord_user_steam (user_id, steam_id)
        ON DELETE CASCADE
);

-- Foreign key indexing
CREATE INDEX ix_discord_channel_guild_id ON discord_channel (guild_id);
CREATE INDEX ix_discord_member_steam_discord_user_steam
    ON discord_member_steam (user_id, steam_id);
