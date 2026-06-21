# Features

## `POST /features`

Cria uma feature flag.

Request:

```json
{
  "name": "Checkout Upsell",
  "key": "checkout_upsell",
  "description": "Oferta incremental no checkout",
  "enabled": true,
  "rollout_percentage": 45,
  "ml_enabled": true,
  "ml_threshold_mode": "maximize_f1",
  "ml_threshold_value": 0.1
}
```

Response `201`:

```json
{
  "id": 1,
  "name": "Checkout Upsell",
  "key": "checkout_upsell",
  "description": "Oferta incremental no checkout",
  "enabled": true,
  "rollout_percentage": 45,
  "ml_enabled": true,
  "ml_threshold_mode": "maximize_f1",
  "ml_threshold_value": 0.1,
  "created_at": "2026-05-23T12:00:00Z",
  "updated_at": "2026-05-23T12:00:00Z"
}
```

## `GET /features`

Lista features ordenadas por criação.

Cada item expõe:

- `name`: nome legível da regra;
- `key`: identificador técnico usado em eventos e avaliação;
- `description`: descrição curta opcional;
- `rollout_percentage`: percentual de liberação gradual;
- `ml_enabled`: se a avaliação pode usar ML;
- `ml_threshold_mode`: política do corte de liberação.

## `GET /features/{feature_id}`

Busca feature por ID.

## `PUT /features/{feature_id}`

Atualiza feature existente.

Request usa o mesmo schema de criação (`FeatureCreate`).

## `DELETE /features/{feature_id}`

Remove feature.

Response: `204 No Content`.
