-- name: InsertUser :one
INSERT INTO users (username, password_hash) VALUES (?,?)
RETURNING id;

-- name: InsertAnonymousUser :exec
INSERT OR IGNORE INTO users (id, username) VALUES (0, "anonymous");

-- name: InsertPaste :one
INSERT INTO pastes (owner_id,slug,content) VALUES (?,?,?)
RETURNING id;

-- name: InsertPasteAttachment :one
INSERT INTO attachments (paste_id,slug) VALUES (?,?)
RETURNING id;

-- name: GetUserByUsername :one
SELECT * FROM users
WHERE username = ? LIMIT 1;

-- name: GetLatestPastes :many
SELECT p.id, p.owner_id, p.slug, users.username FROM pastes as p
INNER JOIN users ON users.id = p.owner_id
ORDER BY p.id DESC
LIMIT ?;

-- name: GetLatestPastesByUser :many
SELECT p.id, p.owner_id, p.slug FROM pastes as p
INNER JOIN users ON users.id = p.owner_id
WHERE users.username = ?
ORDER BY p.id DESC;

-- name: GetPasteBySlug :one
SELECT pastes.* FROM pastes
INNER JOIN users ON users.id = pastes.owner_id
WHERE users.username = ? AND pastes.slug = ?
LIMIT 1;

-- name: GetAttachmentsByPasteID :many
SELECT * FROM attachments
WHERE paste_id = ?;

-- name: GetAttachmentBySlug :one
SELECT attachments.* FROM attachments
INNER JOIN users ON users.id = pastes.owner_id
INNER JOIN pastes ON attachments.paste_id = pastes.id
WHERE users.username = ? AND pastes.slug = sqlc.arg(paste_slug) AND attachments.slug = sqlc.arg(attachment_slug)
LIMIT 1;
