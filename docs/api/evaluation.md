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
