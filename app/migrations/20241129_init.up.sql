CREATE TABLE users (
    id            INTEGER PRIMARY KEY,
    username      TEXT    NOT NULL UNIQUE,
    password_hash BLOB
);

CREATE TABLE pastes (
    id      INTEGER PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    slug    TEXT    NOT NULL,
    content TEXT    NOT NULL,
    UNIQUE(owner_id, slug),
    FOREIGN KEY(owner_id) REFERENCES users(id)
);

CREATE TABLE attachments (
    id      INTEGER PRIMARY KEY,
    paste_id INTEGER NOT NULL,
    slug    TEXT    NOT NULL,
    UNIQUE(paste_id, slug),
    FOREIGN KEY(paste_id) REFERENCES pastes(id)
);
