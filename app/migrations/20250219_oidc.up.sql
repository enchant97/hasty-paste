CREATE TABLE
  oidc_users (
    id INTEGER PRIMARY KEY,
    user_id UUID NOT NULL,
    client_id TEXT NOT NULL,
    user_sub TEXT NOT NULL,
    UNIQUE (user_id, client_id),
    UNIQUE (client_id, user_sub),
    FOREIGN KEY (user_id) REFERENCES users (id)
  );

CREATE UNIQUE INDEX oidc_client_sub_idx ON oidc_users (client_id, user_sub);
