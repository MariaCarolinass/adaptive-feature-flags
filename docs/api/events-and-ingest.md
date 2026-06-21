# Events e Ingest

## `POST /events`

Registra um evento individual.

Request:

```json
{
  "source": "web_app",
  "user_id": "user_123",
  "feature_key": "checkout_upsell",
  "event_type": "checkout_upsell_shown",
  "timestamp": "2026-05-23T12:00:00Z",
  "properties": {
    "activity_name": "Viu oferta no checkout",
    "page": "cart"
  }
}
```

## `GET /events`

Lista eventos com filtros opcionais:

- `user_id`
- `feature_key`
- `event_type` - identificador técnico da atividade

## `POST /ingest/events`

Ingestão canônica em lote para integração com sistemas externos.

Request:

```json
{
  "source": "web_app",
  "events": [
    {
      "user_id": "user_123",
      "feature_key": "checkout_upsell",
      "event_type": "checkout_upsell_shown",
      "timestamp": "2026-05-23T12:00:00Z",
      "properties": {
        "activity_name": "Viu oferta no checkout",
        "page": "cart"
      }
    },
    {
      "user_id": "user_123",
      "feature_key": "checkout_upsell",
      "event_type": "checkout_upsell_clicked",
      "timestamp": "2026-05-23T12:01:10Z",
      "properties": {
        "activity_name": "Clicou na oferta do checkout",
        "platform": "ios"
      }
    }
  ]
}
```

Observação:

- `event_type` guarda o identificador técnico da atividade.
- O nome amigável pode ser salvo em `properties.activity_name`.

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
- `latency_ms` em `properties`, quando presente, deve ficar entre `0` e `120000`.
- Quando houver experimento A/B ativo para a `feature_key`, a API anexa `ab_variant` no evento persistido.
- A API continua processando o lote e retorna `saved_events` e `rejected`.
