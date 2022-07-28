# REST API
This app has a REST API that can allow easy access of functions through automation.

The REST API is documented internally using openapi. You can access swagger docs by going to "/api/docs".

## Docs Routes
- `/api/docs`
- `/api/redocs`
- `/api/openapi.json`

## API Routes
### GET /api/is-healthy
Get the status of the server


#### Response, 200
```
🆗
```

### POST /api/pastes
Create a new paste.

#### Request
```json
{
  "content": "string",
  "expire_dt": "2022-07-28T11:21:19.839Z",
  "long_id": false
}
```

#### Response, 200
```json
{
  "creation_dt": "2022-07-28T11:22:20.080Z",
  "expire_dt": "2022-07-28T11:22:20.080Z",
  "paste_id": "string"
}
```

### GET /api/pastes/{paste id}
Returns the raw paste file, direct from [flat file](flat-file-format.md).

### GET /api/pastes{paste id}/content
Returns the pastes content.

### GET /api/pastes{paste id}/meta
Returns the paste's meta as JSON.

#### Response, 200
```json
{
  "creation_dt": "2022-07-28T11:22:20.080Z",
  "expire_dt": "2022-07-28T11:22:20.080Z",
  "paste_id": "string"
}
```
