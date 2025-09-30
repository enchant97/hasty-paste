-- name: InsertUser :one
INSERT INTO users (id,username, password_hash) VALUES (?,?,?)
RETURNING id;

-- name: InsertAnonymousUser :exec
INSERT OR IGNORE INTO users (id, username) VALUES (?, "anonymous");

-- name: InsertOIDCUser :exec
INSERT INTO oidc_users (user_id, client_id, user_sub) VALUES (?,?,?);

-- name: GetUserByID :one
SELECT * FROM users
WHERE id = ? AND deleted_at IS NULL
LIMIT 1;

-- name: GetUserByUsername :one
SELECT * FROM users
WHERE username = ? AND deleted_at IS NULL
LIMIT 1;

-- name: GetUserByOIDC :one
SELECT u.* FROM oidc_users AS o
INNER JOIN users AS u ON u.id = o.user_id
WHERE client_id = ? AND user_sub = ? AND u.deleted_at IS NULL
LIMIT 1;

-- name: MarkUserAsDeletedByID :exec
UPDATE users
SET deleted_at = CURRENT_TIMESTAMP
WHERE id = ?;
