CREATE TABLE users (
    id        INTEGER PRIMARY KEY,
    username  TEXT    NOT NULL UNIQUE
);

CREATE TABLE pastes (
    id        INTEGER PRIMARY KEY,
    ownerId   INTEGER NOT NULL,
    slug      TEXT    NOT NULL,
    UNIQUE(ownerId, slug),
    FOREIGN KEY(ownerId) REFERENCES users(id)
);

CREATE TABLE attachments (
    id        INTEGER PRIMARY KEY,
    pasteId   INTEGER NOT NULL,
    slug      TEXT    NOT NULL,
    UNIQUE(pasteId, slug),
    FOREIGN KEY(pasteId) REFERENCES pastes(id)
);
