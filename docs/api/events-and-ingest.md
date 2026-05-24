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

Regras de robustez aplicadas na ingestão:

- Eventos com timestamp no futuro são rejeitados.
- Campos obrigatórios vazios/inválidos são rejeitados.
- Métricas operacionais opcionais em `properties` são validadas:
  - `latency_ms` entre `0` e `120000`
  - `error_rate` entre `0` e `1`
  - `cpu_pct` entre `0` e `100`
  - `mem_pct` entre `0` e `100`
- Quando houver experimento A/B ativo para a `feature_key`, a API anexa `ab_variant` no evento persistido.
- A API continua processando o lote e retorna `saved_events` e `rejected`.
