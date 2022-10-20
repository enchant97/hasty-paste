# REST API
This app has a REST API that can allow easy access of functions through automation.

- Download the OpenAPI spec [here](assets/openapi.yml)
- View docs internally by going to:
  - `/api/docs`
  - `/api/redocs`
  - `/api/openapi.json`


## Simple Paste API
Simple paste provides a very easy way of creating a paste from the cli using curl.

For Example:

```
$ curl -X POST --data-binary @my-file.txt https://hasty-paste/api/pastes/simple
rcCnCAgERz
```
