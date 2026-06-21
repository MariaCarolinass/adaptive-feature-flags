# Evaluation

## `POST /evaluate`

Endpoint de decisão por usuário, otimizado para baixa latência.

Regras de alto nível:

- Tenta usar machine learning quando `ml_enabled=true`, o modelo está `ready` e existe `artifact_path`.
- Aplica fallback para rollout determinístico quando a pontuação não está disponível.
- Não treina modelo e não reprocessa histórico.

Request:

```json
{
  "feature_key": "checkout_upsell",
  "user": {
    "user_id": "user_123"
  }
}
```

Exemplo de resposta com machine learning:

```json
{
  "feature_key": "checkout_upsell",
  "user_id": "user_123",
  "activity": "checkout_upsell_shown",
  "enabled": true,
  "decision_source": "ml",
  "score": 0.42,
  "threshold": 0.2,
  "threshold_mode": "fixed",
  "experiment": {
    "experiment_id": 1,
    "experiment_name": "Checkout Upsell A/B",
    "variant": "B"
  },
  "model_version": "v1"
}
```

`threshold_mode` suportados:

- `fixed`
- `match_rollout`
- `maximize_f1` (usa o melhor threshold encontrado no treino)

Exemplo de resposta com fallback:

```json
{
  "feature_key": "checkout_upsell",
  "user_id": "user_123",
  "activity": "checkout_upsell_shown",
  "enabled": false,
  "decision_source": "rollout",
  "score": null,
  "threshold": null,
  "threshold_mode": null,
  "experiment": null,
  "model_version": null
}
```

Valores possíveis de `decision_source`:

- `feature_not_found`
- `feature_disabled`
- `ml`
- `rollout`

`activity` indica o identificador técnico do evento mais recente encontrado para aquele `user_id` e `feature_key`.
Quando não houver evento compatível, o campo pode vir `null`.

O campo `experiment` é opcional e aparece quando existe experimento ativo para a regra.

Histórico de decisões e limpeza de registros estão em [`evaluations.md`](evaluations.md).
