# 0002 - Safe Fallback to Deterministic Rollout

- Status: Accepted
- Data: 2026-05-23

## Contexto

Decisão por machine learning pode falhar por ausência de dados, artefato indisponível ou erro de inferência. O sistema não pode bloquear avaliação de feature por isso.

## Decisão

Sempre aplicar fallback para rollout determinístico quando machine learning não for aplicável ou falhar.

## Consequencias

- Positivas: alta disponibilidade de decisão e comportamento previsível.
- Negativas: menor uso efetivo de machine learning em cenários com dados insuficientes.
- Riscos: equipe interpretar fallback frequente como comportamento esperado e não investigar causa raiz.
