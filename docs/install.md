# Install
This section will demonstrate how Paste Bin can be installed and configured.

## Configuration
All configs shown here should be given as environment variables.

| Name          | Description                                   | Default       | Docker Default |
| :------------ | :-------------------------------------------- | :------------ | :------------- |
| PASTE_ROOT    | Where the paste flat file system will be kept |               | /app/data      |
| MAX_BODY_SIZE | The max body size, given in bytes             | 2000000       | 2000000        |
| WORKERS       | Number of separate processes to spawn         | (Docker Only) | 1              |
| CERT_FILE     | SSL certificate file path (public)            | (Docker Only) | -              |
| KEY_FILE      | SSL key file path (private)                   | (Docker Only) | -              |

> Default values indicated with '-' are not required

> If you want HTTPS, both `CERT_FILE` and `KEY_FILE` environment values must be provided to valid certificates

> If you are expecting heavy load set `WORKERS` to how many physical cpu cores are available.


## With Docker (Recommended)
This will assume you have both Docker and Docker Compose installed.

1. Create directory for app
2. Create file called `docker-compose.yml` inside folder
3. Copy example compose file shown below
4. Run `docker compose up -d` inside folder
5. Paste Bin is now running

```yml
version: "3"

services:
  paste-bin:
    container_name: paste-bin
    image: ghcr.io/enchant97/paste-bin:1
    restart: unless-stopped
    volumes:
      - data:/app/data
    ports:
      - 8000:8000

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
git clone https://github.com/enchant97/paste-bin

cd paste-bin

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

hypercorn 'paste_bin.main:create_app()' --bind 0.0.0.0:8000 --workers 1
```

If you wish to configure Hypercorn the documentation can be found [here](https://pgjones.gitlab.io/hypercorn/), you could for example configure https or different bind methods.
