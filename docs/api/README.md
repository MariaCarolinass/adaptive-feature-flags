# API Reference

Documentação funcional dos endpoints expostos pela API.

## Índice

- `health-and-root.md`
- `features.md`
- `events-and-ingest.md`
- `evaluation.md`
- `training-and-model-status.md`
- `simulation.md`

## Convenções

- Base URL local: `http://localhost:8000`
- Formato padrão: `application/json` (exceto `POST /simulate`, que usa `multipart/form-data`)
- Erro interno padrão: `500 {"detail":"Internal server error."}`
