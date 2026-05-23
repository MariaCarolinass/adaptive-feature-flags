# 0005 - Treino assíncrono com worker único e retenção de jobs

- Status: Accepted
- Data: 2026-05-23

## Contexto

O MVP precisa executar treino assíncrono sem complexidade de fila distribuída, mantendo rastreabilidade de jobs e custo operacional baixo.

## Decisão

Usar `TrainingJobService` com `ThreadPoolExecutor` de `max_workers=1`, persistência de status em `training_jobs` e pruning por `max_jobs`/`retention_minutes`.

## Consequências

- Positivas: implementação simples, previsível e suficiente para MVP.
- Negativas: sem paralelismo de treino.
- Riscos: fila crescer em picos de uso, aumentando tempo de espera.

## Alternativas consideradas

1. Multiprocesso local com vários workers.
2. Fila externa (ex.: Celery/RQ) com workers distribuídos.
