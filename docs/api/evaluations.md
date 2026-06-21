# Evaluations

## `GET /evaluations`

Retorna o histórico de decisões salvas no backend, do mais recente para o mais antigo.

Query params:

- `limit` - quantidade máxima de itens retornados, padrão `1000`

Exemplo de resposta:

```json
[
  {
    "id": 12,
    "created_at": "2026-06-04T14:19:00+00:00",
    "feature_key": "checkout_upsell",
    "user_id": "user_123",
    "activity": "checkout_upsell_shown",
    "enabled": true,
    "decision_source": "ml",
    "score": 0.81,
    "threshold": 0.2,
    "threshold_mode": "fixed",
    "experiment": null,
    "model_version": "v1"
  }
]
```

## `DELETE /evaluations`

Remove todo o histórico salvo de avaliações.

Resposta:

```json
{ "deleted": 12 }
```
