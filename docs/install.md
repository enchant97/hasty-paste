# Install
This section will demonstrate how Hasty Paste can be installed and configured.

## Important Notes
Please read these notes before continuing.

- Running on a filesystem that is case-insensitive is **not** supported
- Running multiple instances is supported, you could even use rsync to sync between multiple file systems.
- The paste root directory must have read/write permissions for the user running the app
- Access to add and read pastes is public, use a reverse proxy to add authentication
- A HTTPS connection at endpoint is required for the "Copy Share Link" button
- Use HTTPS otherwise paste links are exposed to man-in-the-middle attacks
- If you have a high amount of clients, use Redis caching and set `WORKERS` to match the physical cpu cores

## Configuration
All configs shown here should be given as environment variables.

| Name                             | Description                                                        | Default       | Docker Default |
| :------------------------------- | :----------------------------------------------------------------- | :------------ | :------------- |
| PASTE_ROOT                       | Where the paste flat file system will be kept                      |               | /app/data      |
| TIME_ZONE                        | The time-zone where your clients are (used in web UI)              | Europe/London | Europe/London  |
| NEW_AT_INDEX                     | Index page displays new paste page instead                         | False         | False          |
| ENABLE_PUBLIC_LIST               | Whether to enable public access for listing pastes                 | False         | False          |
|                                  |                                                                    |               |                |
| UI_DEFAULT__USE_LONG_ID          | Setting this to "True" or "False" hides the long id checkbox in UI | -             | -              |
| UI_DEFAULT__EXPIRE_TIME__ENABLE  | Enable a default expire time in web ui                             | False         | False          |
| UI_DEFAULT__EXPIRE_TIME__MINUTES | Default minutes in ui for expiry if enabled                        | 0             | 0              |
| UI_DEFAULT__EXPIRE_TIME__HOURS   | Default hours in ui for expiry if enabled                          | 1             | 1              |
| UI_DEFAULT__EXPIRE_TIME__DAYS    | Default days in ui for expiry if enabled                           | 0             | 0              |
|                                  |                                                                    |               |                |
| CACHE__ENABLE                    | Whether to enable caching of any type                              | True          | True           |
| CACHE__INTERNAL_MAX_SIZE         | The max size of the internal cache (<=0 to disable)                | 4             | 4              |
| CACHE__REDIS_URI                 | Use redis for caching                                              | -             | -              |
|                                  |                                                                    |               |                |
| BRANDING__TITLE                  | Customise the app title                                            | -             | -              |
| BRANDING__DESCRIPTION            | Customise the app description                                      | -             | -              |
| BRANDING__ICON                   | Customise the app icon, provide as absolute filepath               | -             | -              |
| BRANDING__FAVICON                | Customise the app favicon, provide as absolute filepath            | -             | -              |
| BRANDING__CSS_FILE               | Customise the site theme, using a provided css file                | -             | -              |
| BRANDING__HIDE_VERSION           | Hide the app version number                                        | False         | False          |
|                                  |                                                                    |               |                |
| MAX_BODY_SIZE                    | The max body size, given in bytes                                  | 2000000       | 2000000        |
| LOG_LEVEL                        | What log level to use                                              | "WARNING"     | "WARNING"      |
|                                  |                                                                    |               |                |
| WORKERS                          | Number of separate processes to spawn                              | (Docker Only) | 1              |
| CERT_FILE                        | SSL certificate file path (public)                                 | (Docker Only) | -              |
| KEY_FILE                         | SSL key file path (private)                                        | (Docker Only) | -              |

> Default values indicated with '-' are not required

> If you want HTTPS, both `CERT_FILE` and `KEY_FILE` environment values must be provided to valid certificates

> If you are expecting heavy load set `WORKERS` to how many physical cpu cores are available.

### Redis Uri
The `CACHE__REDIS_URI` can only accept certain formats, these are shown below:

- `redis://[[username]:[password]]@localhost:6379/0`
- `rediss://[[username]:[password]]@localhost:6379/0`
- `unix://[[username]:[password]]@/path/to/socket.sock?db=0`

e.g

```
CACHE__REDIS_URI="redis://localhost:6379"
```

### Cache
Hasty Paste supports tired caching. For example both the internal cache and Redis cache can be used. The priority of the cache types are shown below:

```
Internal -> Redis -> Miss
```

If you are using multiple workers (set via `WORKERS`), each worker does **not** share memory. This means when using the internal cache, each cached item will be duplicated across workers (increasing memory usage). If this is the case you may want to use Redis and select a smaller internal cache size.

## With Docker (Recommended)
This will assume you have both Docker and Docker Compose installed.

1. Create directory for app
2. Create file called `docker-compose.yml` inside folder
3. Copy example compose file shown below
4. Run `docker compose up -d` inside folder
5. Hasty Paste is now running

```yml
version: "3"

services:
  paste-bin:
    container_name: paste-bin
    image: ghcr.io/enchant97/hasty-paste:1
    restart: unless-stopped
    volumes:
      - data:/app/data
    ports:
      - 8000:8000
    environment:
      - "UI_DEFAULT__USE_LONG_ID=False"
      - "TIME_ZONE=Europe/London"

volumes:
  data:
```

### With Redis

```yml
version: "3"

services:
  redis:
    container_name: redis
    image: redis:alpine
    restart: unless-stopped

  paste-bin:
    container_name: paste-bin
    image: ghcr.io/enchant97/hasty-paste:1
    restart: unless-stopped
    volumes:
      - data:/app/data
    ports:
      - 8000:8000
    environment:
      - "UI_DEFAULT__USE_LONG_ID=False"
      - "TIME_ZONE=Europe/London"
      - "CACHE__REDIS_URI=redis://redis:6379"
    depends_on:
      - redis

volumes:
  data:
```

## Without Docker
This will assume the supported Python version is installed and accessible.

1. Clone the repository
2. Create virtual Python environment
3. Install requirements
4. Run the app

```
git clone https://github.com/enchant97/hasty-paste

cd paste-bin

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

hypercorn 'paste_bin.main:create_app()' --bind 0.0.0.0:8000 --workers 1
```

If you wish to configure Hypercorn the documentation can be found [here](https://hypercorn.readthedocs.io/), you could for example configure https or different bind methods.
