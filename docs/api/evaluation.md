# Evaluation

## `POST /evaluate`

Endpoint de decisão online por usuário, otimizado para baixa latência.

Regras de alto nível:

- Tenta decisão por machine learning quando `ml_enabled=true` e modelo `ready`.
- Aplica fallback para rollout determinístico se machine learning não estiver disponível.

Request:

```json
{
  "feature_key": "new_checkout",
  "user": {
    "user_id": "user_123"
  }
}
```

Exemplo de resposta com machine learning:

```json
{
  "feature_key": "new_checkout",
  "user_id": "user_123",
  "activity": "viewed_feature",
  "enabled": true,
  "decision_source": "ml",
  "score": 0.42,
  "threshold": 0.2,
  "threshold_mode": "fixed",
  "experiment": {
    "experiment_id": 1,
    "experiment_name": "Checkout CTA A/B",
    "variant": "B"
  },
  "model_version": "v1"
}
```

`threshold_mode` suportados:

- `fixed`
- `match_rollout`
- `maximize_f1` (usa threshold calibrado salvo no treino)

Exemplo de resposta com fallback:

```json
{
  "feature_key": "new_checkout",
  "user_id": "user_123",
  "activity": "viewed_feature",
  "enabled": false,
  "decision_source": "rollout",
  "score": null,
  "model_version": null
}
```

Valores possíveis de `decision_source`:

- `feature_not_found`
- `feature_disabled`
- `ml`
- `rollout`

`activity` indica a atividade mais recente do usuário para a regra avaliada.
Quando não houver evento compatível, o campo pode vir `null`.

## `GET /evaluations`

Retorna o histórico salvo no backend, do mais recente para o mais antigo.

Query params:

- `limit` - quantidade máxima de itens retornados, padrão `1000`

Exemplo de resposta:

```json
[
  {
    "id": 12,
    "created_at": "2026-06-04T14:19:00+00:00",
    "feature_key": "new_checkout",
    "user_id": "user_123",
    "activity": "viewed_feature",
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
