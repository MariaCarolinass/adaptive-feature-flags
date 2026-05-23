# Roadmap

## Fase 0 (atual) - MVP validado

- API funcional para features, events, ingest, evaluate, train e simulate.
- Fallback determinístico em produção.
- Treino síncrono e assíncrono com persistência de jobs.
- Base documental inicial estruturada.

## Fase 1 - Robustez operacional

- Métricas de negócio e técnicas por endpoint.
- Versionamento explícito de modelo e política de rollback.
- Validação semântica mais forte para ingestão canônica.
- Hardening de segurança e limites de taxa por rota sensível.

## Fase 2 - Inteligência de decisão

- Calibração de threshold por feature/segmento.
- Estratégias de recomendação com maior explainability.
- Comparação contínua de baseline de rollout vs machine learning.
- Política automática de re-treino orientada por drift.

## Fase 3 - Plataforma evolutiva

- Integrações nativas com fontes externas de eventos.
- Painel de observabilidade e decisão.
- Governança de experimentos e trilha de auditoria.
- Estratégia de escalabilidade além de SQLite para workloads maiores.
