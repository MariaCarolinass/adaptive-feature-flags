# Experimentação e Teste A/B

## Papel no projeto

O Adaptive Feature Flags usa experimentação para validar se uma mudança realmente melhora o comportamento observado. No MVP, isso complementa o rollout gradual e a decisão por machine learning.

## Relação entre eventos e teste A/B

- `Orientado a eventos`: usa sinais reais de uso para apoiar decisões.
- `Teste A/B`: compara variantes para medir impacto em uma métrica de negócio.

No produto, isso serve para:

- entender se uma mudança performa melhor do que a atual;
- reduzir risco antes de ampliar uma liberação;
- apoiar decisões de rollout com evidência.

## O que o MVP oferece hoje

- rollout determinístico por percentual;
- ingestão de eventos com registro de variante quando há experimento ativo;
- atribuição estável de usuário para A ou B;
- avaliação por machine learning com fallback seguro;
- resumo do experimento com amostras, taxa de sucesso e decisão.

## O que ainda não faz parte do MVP

- A/B/n nativo;
- significância estatística formal;
- guardrails automáticos;
- dashboard completo de experimentação.

## Por que isso importa

A comparação A/B ajuda a transformar opinião em evidência prática. Em vez de decidir apenas por intuição, o produto passa a observar o efeito real de uma variante sobre a métrica escolhida.

## Direção de evolução

1. Modelar hipóteses e métricas de forma explícita.
2. Ampliar a análise causal.
3. Adicionar critérios formais de parada.
4. Integrar experimentação com a evolução do rollout.

Detalhes técnicos do fluxo, cálculo e critérios de decisão estão em [`docs/implementation/experiment-decision-flow.md`](../implementation/experiment-decision-flow.md).
