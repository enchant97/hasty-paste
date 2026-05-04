---
title: "API"
---

Hasty Paste features a REST API, allowing for integration with other services/clients.

## Quick API
This section documents the quick-api. An easy to use interface that can be used easily with programs such as curl.

### Quick Paste Creation
To create a quick paste, with no attachment support. The below curl command could be used:

```
curl -X POST -d "Hello World!" https://paste.example.com/api/q/
```

This will create a public paste under the anonymous user; using: the default expiry, `plaintext` content format and randomly generate a slug. The full paste url will be returned in the response.

This API route will not function if anonymous pastes are disabled.
