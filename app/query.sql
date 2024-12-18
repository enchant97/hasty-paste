-- name: InsertUser :one
INSERT INTO users (username) VALUES (?)
RETURNING id;

-- name: InsertAnonymousUser :exec
INSERT OR IGNORE INTO users (id, username) VALUES (0, "anonymous");

-- name: InsertPaste :one
INSERT INTO pastes (ownerId,slug,content) VALUES (?,?,?)
RETURNING id;

-- name: InsertPasteAttachment :one
INSERT INTO attachments (pasteId,slug) VALUES (?,?)
RETURNING id;

-- name: GetUserByUsername :one
SELECT * FROM users
WHERE username = ? LIMIT 1;

-- name: GetLatestPastes :many
SELECT pastes.*, users.username FROM pastes
INNER JOIN users ON users.id = pastes.ownerId
ORDER BY pastes.id DESC
LIMIT ?;

-- name: GetLatestPastesByUser :many
SELECT pastes.* FROM pastes
INNER JOIN users ON users.id = pastes.ownerId
WHERE users.username = ?
ORDER BY pastes.id DESC;

-- name: GetPasteBySlug :one
SELECT pastes.* FROM pastes
INNER JOIN users ON users.id = pastes.ownerId
WHERE users.username = ? AND pastes.slug = ?
LIMIT 1;

-- name: GetAttachmentsByPasteId :many
SELECT * FROM attachments
WHERE pasteId = ?;

-- name: GetAttachmentBySlug :one
SELECT attachments.* FROM attachments
INNER JOIN users ON users.id = pastes.ownerId
INNER JOIN pastes ON attachments.pasteId = pastes.id
WHERE users.username = ? AND pastes.slug = sqlc.arg(paste_slug) AND attachments.slug = sqlc.arg(attachment_slug)
LIMIT 1;
