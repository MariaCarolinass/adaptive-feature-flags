# `experiments`

Endpoints para cadastrar, listar e acompanhar testes A/B-lite associados a uma `feature_key`.

## Contrato geral

- O teste é ligado a uma única `feature_key`.
- A variante é atribuída de forma determinística por `user_id` e `experiment_id`.
- Quando o experimento está ativo, a ingestão grava `ab_variant` em `properties`.
- O resultado considera somente eventos que já possuem `ab_variant`.
- Eventos antigos sem variante não entram automaticamente no cálculo.

## `POST /experiments`

Cria um teste A/B-lite.

Request:

```json
{
  "name": "Checkout Upsell A/B",
  "feature_key": "checkout_upsell",
  "primary_metric_event": "checkout_upsell_shown",
  "min_samples_per_variant": 100,
  "min_lift": 0.02,
  "enabled": true
}
```

Campos principais:

- `name`: nome do teste.
- `feature_key`: identificador da regra avaliada.
- `primary_metric_event`: identificador da atividade usada como sucesso.
- `min_samples_per_variant`: mínimo de eventos por variante antes de permitir decisão.
- `min_lift`: diferença mínima entre B e A para encerrar o teste.
- `enabled`: ativa ou desativa o teste.

Response: `ExperimentResponse`

## `GET /experiments`

Lista os testes cadastrados.

Response: `list[ExperimentResponse]`

## `GET /experiments/{experiment_id}/result`

Retorna o resultado atual do teste.

### Como o resultado é calculado

O serviço:

1. busca o teste;
2. lê os eventos da `feature_key` associada;
3. separa os eventos por `ab_variant` (`A` e `B`);
4. conta amostras e eventos de sucesso por variante;
5. calcula `rate_a` e `rate_b`;
6. calcula `lift_b_vs_a = rate_b - rate_a`;
7. aplica a regra de decisão.

### Regra de decisão

- Se `A` ou `B` não atingirem `min_samples_per_variant`, a decisão é `continue`.
- Se `abs(lift_b_vs_a) < min_lift`, a decisão é `continue`.
- Se `lift_b_vs_a > 0`, a decisão é `stop_promote_b`.
- Se `lift_b_vs_a < 0`, a decisão é `stop_keep_a`.

### Campos da resposta

- `experiment_id`
- `experiment_name`
- `feature_key`
- `primary_metric_event`
- `variant_stats`
- `user_stats`
- `rate_a`
- `rate_b`
- `lift_b_vs_a`
- `min_lift`
- `min_samples_per_variant`
- `decision`

`decision` usa valores técnicos:

- `continue`: ainda não há critério suficiente para encerrar.
- `stop_promote_b`: a variante B deve ser promovida.
- `stop_keep_a`: a variante A deve ser mantida.

Na UI, esses valores aparecem como:

- `continue` -> `Em andamento`
- `stop_promote_b` -> `Escolher B`
- `stop_keep_a` -> `Manter A`

### Exemplo de resposta

```json
{
  "experiment_id": 1,
  "experiment_name": "Checkout Upsell A/B",
  "feature_key": "checkout_upsell",
  "primary_metric_event": "checkout_upsell_shown",
  "variant_stats": {
    "A": {"samples": 120, "positives": 40},
    "B": {"samples": 118, "positives": 54}
  },
  "user_stats": {
    "A": {"users": 88},
    "B": {"users": 85}
  },
  "rate_a": 0.3333,
  "rate_b": 0.4576,
  "lift_b_vs_a": 0.1243,
  "min_lift": 0.02,
  "min_samples_per_variant": 100,
  "decision": "continue"
}
```

## Observações

- `variant_stats.A.samples` e `variant_stats.B.samples` contam apenas eventos com `ab_variant`.
- `positives` conta eventos cujo `event_type` é igual ao `primary_metric_event`.
- O endpoint não reprocessa eventos sem variante.
- O resultado é um resumo atual do experimento, não um histórico de todas as execuções.
