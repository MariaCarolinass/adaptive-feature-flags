# Events e Ingest

## `POST /events`

Registra um evento individual.

Request:

```json
{
  "source": "web_app",
  "user_id": "user_123",
  "feature_key": "new_checkout",
  "event_type": "view",
  "timestamp": "2026-05-23T12:00:00Z",
  "properties": {
    "page": "checkout"
  }
}
```

## `GET /events`

Lista eventos com filtros opcionais:

- `user_id`
- `feature_key`
- `event_type`

## `POST /ingest/events`

Ingestão canônica em lote para integração com sistemas externos.

Request:

```json
{
  "source": "web_app",
  "events": [
    {
      "user_id": "user_123",
      "feature_key": "new_checkout",
      "event_type": "view",
      "timestamp": "2026-05-23T12:00:00Z",
      "properties": {
        "page": "checkout"
      }
    },
    {
      "user_id": "user_123",
      "feature_key": "new_checkout",
      "event_type": "addtocart",
      "timestamp": "2026-05-23T12:01:10Z",
      "properties": {
        "platform": "ios"
      }
    }
  ]
}
```

Response `201`:

```json
{
  "saved_events": 2,
  "rejected": 0
}
```
