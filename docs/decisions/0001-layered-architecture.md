# 0001 - Layered Architecture (DDD lite)

- Status: Accepted
- Data: 2026-05-23

## Contexto

O projeto precisava de uma base simples para MVP, mas com separação suficiente para permitir evolução de regras de domínio e persistência sem refatorações amplas.

## Decisão

Adotar arquitetura em camadas:

- `api` para contratos HTTP.
- `domain` para regras de negócio e contratos de repositório.
- `infrastructure` para detalhes técnicos (SQLite, machine learning, integrações).

## Consequencias

- Positivas: baixo acoplamento entre regras e framework web.
- Negativas: mais arquivos/boilerplate para mudanças simples.
- Riscos: inconsistências entre contrato de repositório e implementação concreta.
