# Experiments (A/B-lite)

## `POST /experiments`

Cria experimento A/B-lite por feature.

Request:

```json
{
  "name": "Checkout CTA A/B",
  "feature_key": "new_checkout",
  "primary_metric_event": "purchase",
  "min_samples_per_variant": 100,
  "min_lift": 0.02,
  "enabled": true
}
```

## `GET /experiments`

Lista experimentos cadastrados.

## `GET /experiments/{experiment_id}/result`

Calcula resultado atual com regra mínima de parada:

- Só permite decisão final quando cada variante atinge `min_samples_per_variant`.
- Com amostra mínima, se `|lift_b_vs_a| >= min_lift`:
  - `stop_promote_b` (B melhor)
  - `stop_keep_a` (A melhor)
- Caso contrário: `continue`.
