---
title: 01 - Install
---

## Docker (Official)
The app is distributed by a Docker image. This guide will assume you are using Docker, however you should be able to run via other container platforms such as: Kubernetes or Podman.

Below is the image path:

```text
ghcr.io/enchant97/hasty-paste
```

The following labels are available:

> TIP: Image labels follow Semantic Versioning

```text
<major>

<major>.<minor>

<major>.<minor>.<patch>
```

Here is an example Docker Compose file:

```yaml
volumes:
  data:

services:
  hasty-paste:
    image: ghcr.io/enchant97/hasty-paste:2
    restart: unless-stopped
    volumes:
      - data:/opt/hasty-paste/data
    environment:
      AUTH_TOKEN_SECRET: "${AUTH_TOKEN_SECRET}"
      SESSION_SECRET: "${SESSION_SECRET}"
      PUBLIC_URL: "http://example.com"
    ports:
      - 80:8080
```

Take a look at the [configuration]({{< ref configuration.md >}}) chapter to find more about the configuration values.

> TIP: It is recommended to use a reverse proxy to provide https and a custom FQDN.

## Bare
Not officially supported, but you should be able to follow the steps that the Dockerfile performs.
