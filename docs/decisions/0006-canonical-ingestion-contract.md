# 0006 - Contrato canônico de ingestão de eventos

- Status: Accepted
- Data: 2026-05-23

## Contexto

O sistema recebe eventos de fontes heterogêneas. Para evitar acoplamento com schemas de fornecedores, o MVP precisa de um formato estável para ingestão.

## Decisão

Padronizar `POST /ingest/events` com payload canônico:

- `source` obrigatório.
- `events[]` com `user_id`, `feature_key`, `event_type`, `timestamp`, `properties`.

Validação no serviço:

- `source` não vazio;
- lote com pelo menos um evento;
- `timestamp` em UTC e não futuro;
- `properties` como objeto;
- `latency_ms`, quando presente, entre `0` e `120000`.

## Consequências

- Positivas: contrato único para múltiplas integrações e menor acoplamento.
- Negativas: o contrato permanece canônico, mas a validação ainda é propositalmente simples.
- Riscos: ingestão de eventos inconsistentes se cliente não seguir convenções de `event_type` e `properties`.

## Alternativas consideradas

1. Endpoint por integração específica.
2. Ingestão totalmente livre sem contrato comum.
