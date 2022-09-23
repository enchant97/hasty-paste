# Usage
## Paste URL
Say we have a paste with the id of: `InRZdveK9g`. This is what the url would look like:

```
https://pastes.example.com/InRZdveK9g
```

What happens if you forget or want to change the syntax highlighting of the paste? We can add a file extension to the end of the paste URL:

```
https://pastes.example.com/InRZdveK9g.py
```

## CLI
Hasty Paste provides a management CLI.

> Please be aware this CLI is experimental, usage may change without notice.

### Access
Depending on how Hasty Paste was installed, usage will vary.

#### Docker
If you have installed through the official Docker image accessing it is simple.

You can create a temporary container, making sure it has the same volume mount as your running instance.

```
docker run --rm -v <volume name>:/app/data --help
```

You can also run the CLI program directly by using docker exec. This avoids creating containers:

```
docker exec <container name> sh cli --help
```

#### Without Docker
Running without Docker is still as simple:

> The PASTE_ROOT environment variable must be set

```
python -m paste_bin.cli --help
```

### Example Commands
This section will just show some example commands that can be given. More are explained in the in-built help.

#### Remove Expired
If you want to ensure expired pasted are removed you can use:

```
cli cleanup -y --expired
```

#### Clean-Up Old Pastes
If you wanted to remove old pastes you can. The following command illustrates removing pastes older than 365 days:

```
cli cleanup -y --older-than 365
```

Extending this command you could also optionally also remove expired pastes at the same time as well:

```
cli cleanup -y --expired --older-than 365
```
