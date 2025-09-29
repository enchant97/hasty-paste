-- name: AdminDeletePasteByID :exec
DELETE FROM pastes WHERE id = ?;

-- name: AdminDeleteAttachmentByID :exec
DELETE FROM attachments WHERE id = ?;

-- name: AdminGetPastesInDateRangeWithLimit :many
SELECT id FROM pastes as p
WHERE created_at < sqlc.arg(before) AND created_at > sqlc.arg(after) AND (sqlc.arg(user_id) = NULL OR sqlc.arg(user_id) = owner_id)
LIMIT 20;

-- name: AdminGetAttachmentsByPasteId :many
SELECT id FROM attachments
WHERE paste_id = ?;

-- name: AdminGetExpiredPastesWithLimit :many
SELECT id FROM pastes
WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
LIMIT 20;

-- name: AdminGetDeletedPastesWithLimit :many
SELECT id FROM pastes
WHERE deleted_at IS NOT NULL
LIMIT 20;
