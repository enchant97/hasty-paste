CREATE TABLE
  users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash BLOB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
  );

CREATE TABLE
  pastes (
    id INTEGER PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    slug TEXT NOT NULL,
    content TEXT NOT NULL,
    content_format TEXT NOT NULL DEFAULT 'plain',
    visibility TEXT NOT NULL DEFAULT 'public',
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (owner_id, slug),
    FOREIGN KEY (owner_id) REFERENCES users (id)
  );

CREATE TABLE
  attachments (
    id UUID PRIMARY KEY,
    paste_id INTEGER NOT NULL,
    slug TEXT NOT NULL,
    mime_type TEXT NOT NULL DEFAULT 'application/octet-stream',
    size INTEGER NOT NULL,
    checksum TEXT NOT NULL,
    UNIQUE (paste_id, slug),
    FOREIGN KEY (paste_id) REFERENCES pastes (id)
  );
