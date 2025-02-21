---
title: 02 - Configuration
---
Configuration of the app is done through environment variables. See the below options:

> TIP A secret can be generated using: `openssl rand -base64 32`

| Key | Description | Default |
|:----|:------------|:--------|
| `BIND__HOST` | What interface to listen on | `127.0.0.1` |
| `BIND__PORT` | What port to listen on | `8080` |
| `OIDC__ENABLED` | Whether OpenID/OAuth2 Is Enabled | `false` |
| `OIDC__NAME` | The provider name (used for UI) | - |
| `OIDC__ISSUER_URL` | The OIDC issuer url | - |
| `OIDC__CLIENT_ID` | The client id | - |
| `OIDC__CLIENT_SECRET` | The client secret | - |
| `PUBLIC_URL` | Public URL where service can be accessed | - |
| `DB_URI` | URI for database connection | - |
| `DATA_PATH` | where paste assets will be stored | - |
| `AUTH_TOKEN_SECRET` | base64 encoded secret | - |
| `AUTH_TOKEN_EXPIRY` | seconds until a token expires | `604800` |
| `SESSION_SECRET` | base64 encoded secret | - |
| `ENABLE_INTERNAL_SIGNUP` | Whether to allow sign-up for internal accounts | `true` |
| `ENABLE_INTERNAL_LOGIN` | Whether to allow login for internal accounts | `true` |

## OIDC
Single-Sign-On is handled via OpenID Connect and OAuth2. To use SSO you must have a compatible provider that supports the following features:

- OpenID Connect (OIDC) Discovery - RFC5785
- Claims
    - `sub`: the users id
    - `name`: a users full name
    - `preferred_username`: the users username, not the email
- Scopes
    - openid
    - profile

Depending on your SSO provider the issuer URL may be different, see below for examples:

Authentik:

```text
https://{example.com}/application/o/{hasty-paste}/
```

## Database URI
Database URIs have to be set in a specific format, see below examples:

SQLite:

```text
sqlite://path/to/db.sqlite
```
