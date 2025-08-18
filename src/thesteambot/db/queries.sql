-- name: add_discord_user :exec
INSERT INTO discord_user (user_id) VALUES ($1) ON CONFLICT DO NOTHING;

-- name: add_discord_guild :exec
INSERT INTO discord_guild (guild_id) VALUES ($1) ON CONFLICT DO NOTHING;

-- name: add_discord_channel :exec
INSERT INTO discord_channel (channel_id, guild_id) VALUES ($1, $2)
ON CONFLICT DO NOTHING;

-- name: add_discord_member :exec
INSERT INTO discord_member (guild_id, user_id) VALUES ($1, $2)
ON CONFLICT DO NOTHING;

-- name: add_steam_user :exec
INSERT INTO steam_user (user_id) VALUES ($1);

-- name: delete_steam_user :exec
DELETE FROM steam_user WHERE user_id = $1;

-- name: add_discord_user_steam :exec
INSERT INTO discord_user_steam (user_id, steam_id) VALUES ($1, $2);

-- name: get_discord_user_steam :many
SELECT * FROM discord_user_steam WHERE user_id = $1;

-- name: add_discord_member_steam :exec
INSERT INTO discord_member_steam (guild_id, user_id, steam_id)
VALUES ($1, $2, $3);

-- name: get_discord_oauth :one
SELECT * FROM discord_oauth WHERE user_id = $1;

-- name: set_discord_oauth :exec
INSERT INTO discord_oauth
(user_id, access_token, token_type, expires_at, refresh_token, scope)
VALUES ($1, $2, $3, $4, $5, $6)
ON CONFLICT (user_id) DO UPDATE SET
    access_token = EXCLUDED.access_token,
    token_type = EXCLUDED.token_type,
    expires_at = EXCLUDED.expires_at,
    refresh_token = EXCLUDED.refresh_token,
    scope = EXCLUDED.scope;

-- name: delete_discord_oauth :exec
DELETE FROM discord_oauth WHERE user_id = $1;
