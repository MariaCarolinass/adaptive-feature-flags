# Features

## `POST /features`

Cria uma feature flag.

Request:

```json
{
  "name": "New Checkout",
  "key": "new_checkout",
  "description": "Checkout variant",
  "enabled": true,
  "rollout_percentage": 10,
  "ml_enabled": true,
  "ml_threshold_mode": "maximize_f1",
  "ml_threshold_value": 0.1
}
```

Response `201`:

```json
{
  "id": 1,
  "name": "New Checkout",
  "key": "new_checkout",
  "description": "Checkout variant",
  "enabled": true,
  "rollout_percentage": 10,
  "ml_enabled": true,
  "ml_threshold_mode": "maximize_f1",
  "ml_threshold_value": 0.1,
  "created_at": "2026-05-23T12:00:00Z",
  "updated_at": "2026-05-23T12:00:00Z"
}
```

## `GET /features`

Lista features ordenadas por criação.

## `GET /features/{feature_id}`

Busca feature por ID.

## `PUT /features/{feature_id}`

Atualiza feature existente.

Request usa o mesmo schema de criação (`FeatureCreate`).

## `DELETE /features/{feature_id}`

Remove feature.

Response: `204 No Content`.
