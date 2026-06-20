# Experiments (A/B-lite)

Esta parte da API serve para criar e acompanhar testes A/B simples por `feature_key`.
O sistema distribui os usuários entre variantes A e B, registra os eventos com a variante
e calcula o resultado com base nos dados coletados depois que o experimento está ativo.

## Como funciona

1. Você cria um experimento para uma `feature_key`.
2. A partir daí, novos eventos dessa regra passam a receber `ab_variant` em `properties`.
3. O sistema divide os usuários em A ou B de forma estável, usando `user_id` e `experiment_id`.
4. O resultado do experimento conta apenas eventos novos que já têm `ab_variant`.
5. A decisão final só acontece quando cada variante atinge a amostra mínima.

Importante:

- eventos antigos não entram automaticamente no cálculo;
- o experimento não altera a regra por conta própria;
- a tela mostra o resumo, mas a coleta acontece na ingestão de eventos;
- o mesmo experimento continua valendo enquanto estiver `enabled=true`.

## `POST /experiments`

Cria experimento A/B-lite por feature.

Request:

```json
{
  "name": "Checkout CTA A/B",
  "feature_key": "new_checkout",
  "primary_metric_event": "viewed_feature",
  "min_samples_per_variant": 100,
  "min_lift": 0.02,
  "enabled": true
}
```

Campos principais:

- `min_samples_per_variant`: amostras mínimas por variante antes de encerrar o teste.
- `min_lift`: diferença mínima entre as variantes para permitir decisão final.
- `primary_metric_event`: atividade usada como sucesso do teste, por exemplo `viewed_feature`.

## O que a variante significa

Para cada evento novo da `feature_key` ativa, o sistema calcula uma variante:

- `A`
- `B`

A atribuição é estável por usuário e experimento. Isso evita que o mesmo usuário fique alternando entre A e B em chamadas diferentes.

## O que entra no resultado

O endpoint de resultado conta somente eventos que:

- pertencem à `feature_key` do experimento;
- têm `ab_variant` salvo em `properties`;
- usam o `primary_metric_event` definido no experimento para marcar sucesso.

O retorno também mostra usuários únicos por variante:

- `user_stats.A.users`
- `user_stats.B.users`

O cálculo retorna:

- quantidade de amostras de A e B;
- quantidade de positivos em A e B;
- quantidade de usuários únicos em A e B;
- taxa de A e B;
- lift de B contra A;
- diferença mínima configurada;
- decisão atual.

## `GET /experiments`

Lista experimentos cadastrados.

## `GET /experiments/{experiment_id}/result`

Calcula resultado atual com regra mínima de parada:

- Só permite decisão final quando cada variante atinge `min_samples_per_variant`.
- Com amostra mínima, se `|lift_b_vs_a| >= min_lift`:
  - `stop_promote_b` (B melhor)
  - `stop_keep_a` (A melhor)
- Caso contrário: `continue`.

## Fluxo prático na UI

Na página de Experimentos:

1. escolha a regra;
2. escolha a métrica principal;
3. defina as amostras mínimas e a diferença mínima;
4. ative o experimento;
5. comece a registrar eventos da mesma regra;
6. abra `Ver resultado` para acompanhar o teste.

Se o resultado ficar zerado, normalmente significa que ainda não chegaram eventos novos com `ab_variant`
ou que a métrica principal ainda não apareceu nos eventos coletados.
