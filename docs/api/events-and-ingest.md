# Events e Ingest

## `POST /events`

Registra uma atividade individual.

Campos obrigatórios:

- `source`
- `user_id`
- `feature_key`
- `event_type`
- `timestamp`
- `properties`

Exemplo:

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

Lista atividades com filtros opcionais:

- `user_id`
- `feature_key`
- `event_type`

`event_type` é o identificador técnico da atividade.

## `POST /ingest/events`

Ingressa um lote de atividades.
O lote aceita até `1000` eventos por requisição.
A API também aplica limite de taxa por cliente/IP para evitar abuso por várias requisições pequenas.

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

Response:

```json
{
  "saved_events": 2,
  "rejected": 0
}
```

## Regras de validação

- `source` não pode estar vazio.
- O lote deve conter ao menos um evento.
- O lote não pode exceder `1000` eventos.
- A API aplica limite de taxa por cliente/IP para bloquear abuso repetido.
- `user_id`, `feature_key` e `event_type` não podem estar vazios.
- `properties` deve ser um objeto.
- `timestamp` deve ser `datetime` com timezone.
- `timestamp` não pode estar no futuro.
- `latency_ms`, quando presente em `properties`, deve ficar entre `0` e `120000`.

## Comportamento

- A API processa o lote até o fim e conta quantos itens foram salvos e rejeitados.
- Cada item válido é persistido individualmente.
- O contrato base de ingestão não inclui `ab_variant`; esse campo só aparece quando há experimento ativo e a ingestão anexa a variante.

## Observações

- O nome amigável da atividade pode ser salvo em `properties.activity_name`.
- O valor em `event_type` continua sendo o identificador técnico usado pelo sistema.
