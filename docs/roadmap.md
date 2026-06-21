# Roadmap

## Status atual

O projeto já cobre o núcleo do produto:

- catálogo de atividades;
- cadastro e gestão de regras;
- registro de eventos e ingestão em lote;
- avaliação online com fallback determinístico;
- treino manual do modelo via `POST /train`;
- experimentos A/B-lite;
- UI web com dashboard;
- SDK Python e exemplos de integração;
- documentação técnica e operacional;

## Fase 1 - Robustez operacional

Prioridades imediatas para reduzir risco de uso real:

- automatizar o treino em batch ou micro-batch;
- migrar SQLite para Postgres quando houver necessidade de concorrência ou múltiplas instâncias;
- adicionar observabilidade de produção para ingestão, treino e avaliação;
- reforçar limites e validações de entrada nas rotas sensíveis;
- manter a UI responsiva em telas pequenas e com tabelas legíveis.

## Fase 2 - Decisão mais inteligente

Evoluções que melhoram a qualidade da recomendação sem quebrar o fluxo atual:

- calibrar `threshold` por feature e por segmento;
- comparar de forma contínua rollout determinístico vs ML;
- incorporar políticas de re-treino por volume, tempo ou drift;
- melhorar explicabilidade da decisão exibida na UI e na API;
- ampliar a taxonomia de atividades sem perder consistência com o dataset.

## Fase 3 - Integração com fontes externas

Quando o produto precisar receber telemetria de sistemas externos:

- integrar SDKs e pipelines de eventos reais como Segment, RudderStack, PostHog ou Snowplow;
- adicionar ingestão assíncrona por fila ou stream;
- permitir normalização de eventos vindos de diferentes origens;
- manter o contrato canônico interno para não acoplar o core a um fornecedor específico.

## Fase 4 - Escala e governança

Evoluções para operação maior e auditoria mais forte:

- versionamento explícito de modelos e políticas de promoção;
- trilha de auditoria para decisões, treino e experimentos;
- painel operacional de métricas e saúde do pipeline;
- suporte a workloads maiores sem depender de SQLite;
- governança de acesso para ambientes e endpoints administrativos.
