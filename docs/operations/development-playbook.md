# Development Playbook

## Setup local

```bash
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env
pip install -r requirements.txt
python3 scripts/seed_demo.py
uvicorn app.main:app --reload
```

## Comandos essenciais

- Rodar testes: `pytest`
- Healthcheck: `curl http://localhost:8000/health`
- Listar features: `curl http://localhost:8000/features`
- Treinar modelo: `curl -X POST http://localhost:8000/train`

## Variaveis de ambiente relevantes

- `DATABASE_URL`
- `MODELS_DIR`
- `ENABLE_DOCS`
- `LOG_LEVEL`
- `POSITIVE_EVENT_TYPES`
- `VIEW_EVENT_TYPES`
- `INTERMEDIATE_POSITIVE_EVENT_TYPES`
- `TERMINAL_POSITIVE_EVENT_TYPES`

## Checklist antes de PR

1. Executar `pytest`.
2. Validar fluxo básico: `features -> events/ingest -> train -> evaluate`.
3. Revisar impacto em fallback (`decision_source`).
4. Atualizar docs em `docs/` quando mudar regra de negócio, endpoint ou comportamento de machine learning.
