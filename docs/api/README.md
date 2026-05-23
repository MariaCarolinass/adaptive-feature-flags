# API Reference

Documentação funcional dos endpoints expostos pela API.

## Índice

- `health-and-root.md`
- `features.md`
- `events-and-ingest.md`
- `evaluation.md`
- `training-and-model-status.md`

## Convenções

- Base URL local: `http://localhost:8000`
- Formato padrão: `application/json`
- Erro interno padrão: `500 {"detail":"Internal server error."}`

## Autenticação

Se `AUTH_ENABLED=true`, os endpoints protegidos exigem JWT bearer token.

- Header aceito:

- `Authorization: Bearer <sua-chave>`

Paths isentos por padrão:

- `/`
- `/health`
- `/auth/token`
- `/docs`
- `/redoc`
- `/openapi.json`

Emissão de token:

- `POST /auth/token` com payload:
  - `issuer_key`
  - `subject` (opcional)
  - `expires_minutes` (opcional)
