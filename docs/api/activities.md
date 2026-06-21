# Activities

## Papel no projeto

A API de atividades mantém o catálogo de atividades usado pela UI e pelos fluxos de
eventos do sistema. Na prática, ela separa:

- `key`: identificador técnico estável;
- `name`: rótulo de exibição;
- `description`: descrição curta.

Esse catálogo é usado como apoio para registro de eventos, avaliação de regras e
preenchimento de opções na interface.

## `POST /activities`

Cria uma atividade.

Request:

```json
{
  "key": "checkout_upsell_shown",
  "name": "Viu oferta no checkout",
  "description": "Oferta incremental exibida no checkout",
  "enabled": true
}
```

Response `201`:

```json
{
  "id": 1,
  "key": "checkout_upsell_shown",
  "name": "Viu oferta no checkout",
  "description": "Oferta incremental exibida no checkout",
  "enabled": true,
  "created_at": "2026-06-18T12:00:00Z",
  "updated_at": "2026-06-18T12:00:00Z"
}
```

## `GET /activities`

Lista as atividades cadastradas, em ordem de criação.

Essa lista alimenta a UI e ajuda a manter o campo `event_type` legível nos fluxos de registro e ingestão.

## `GET /activities/{activity_id}`

Busca uma atividade por ID.

## `PUT /activities/{activity_id}`

Atualiza uma atividade existente.

Request usa o mesmo schema de criação (`ActivityCreate`).

## `DELETE /activities/{activity_id}`

Remove uma atividade.

Response: `204 No Content`.
