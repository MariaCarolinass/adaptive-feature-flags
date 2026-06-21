# 0004 - Threshold de machine learning controlado por feature e modelo

- Status: Accepted
- Data: 2026-05-23

## Contexto

O serviço de avaliação precisa transformar score contínuo de machine learning em decisão binária (`enabled=true/false`) com latência baixa e comportamento determinístico.
O mesmo produto precisa suportar políticas diferentes por feature sem reescrever o fluxo online.

## Decisão

Usar a política de threshold definida pela feature:

- `fixed`: usa `ml_threshold_value`;
- `match_rollout`: aproxima o threshold para acompanhar o rollout percentual;
- `maximize_f1`: usa o melhor threshold encontrado no treino do modelo.

## Consequências

- Positivas: flexibilidade sem perder previsibilidade.
- Negativas: maior necessidade de alinhar treino, feature e documentação.
- Riscos: configuração incoerente entre feature e metadados do modelo gerar decisões menos úteis.

## Alternativas consideradas

1. Limiar 0.5 fixo para todas as features.
2. Um threshold global independente da feature.
