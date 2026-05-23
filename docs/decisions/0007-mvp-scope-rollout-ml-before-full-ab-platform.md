# 0007 - Escopo do MVP: rollout + machine learning antes de plataforma A/B completa

- Status: Accepted
- Data: 2026-05-23

## Contexto

O projeto precisa validar rapidamente a proposta de decisão orientada por eventos sem aumentar complexidade de produto e operação no início.

Uma plataforma A/B completa exige capacidades adicionais (gestão de variantes, estatística inferencial, governança e observabilidade dedicada), elevando custo de implementação e risco de atraso na validação do MVP.

## Decisão

Priorizar no MVP:

- Rollout determinístico por percentual.
- Ingestão de eventos em formato canônico.
- Avaliação por machine learning com fallback seguro.
- Recomendação de rollout com métricas explicáveis.

Adiar para fases posteriores:

- Framework A/B completo com gestão de experimentos e significância estatística.

## Consequências

- Positivas: validação mais rápida da arquitetura Event-Driven e menor custo inicial.
- Negativas: capacidade de experimentação causal ainda limitada no produto.
- Riscos: expectativa de stakeholders sobre recursos A/B além do escopo atual.

## Alternativas consideradas

1. Implementar plataforma A/B completa no MVP.
2. Manter apenas rollout percentual sem machine learning nem recomendação.
