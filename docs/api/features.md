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
  "ml_enabled": true
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

## `GET /features/{feature_key}/recommendation`

Retorna recomendação estratégica de rollout para a feature.

Exemplo de resposta:

```json
{
  "feature_key": "new_checkout",
  "current_rollout": 10,
  "recommendation": "increase_rollout",
  "suggested_rollout": 30,
  "reason": "Machine learning-selected users showed higher engagement than random rollout.",
  "metrics": {
    "ml_engagement": 0.34,
    "rollout_engagement": 0.22,
    "uplift": 0.12,
    "coverage": 0.18
  }
}
```
