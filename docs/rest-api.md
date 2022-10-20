# REST API
This app has a REST API that can allow easy access of functions through automation.

- Download the OpenAPI spec [here](assets/openapi.yml)
- View docs internally by going to:
  - `/api/docs`
  - `/api/redocs`
  - `/api/openapi.json`


## Simple Paste API
Simple paste provides a very easy way of creating a paste from the cli using curl.

You can download the official script [here](https://github.com/enchant97/hasty-paste/blob/main/hastily-paste-it/README.md).

Or use this curl example:

```
$ curl -X POST --data-binary @my-file.txt https://hasty-paste/api/pastes/simple
rcCnCAgERz
```
