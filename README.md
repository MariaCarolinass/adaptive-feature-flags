# Adaptive Feature Flags

Adaptive Feature Flags é uma API de feature flags com rollout determinístico e suporte opcional a machine learning para decisão por usuário, construída com uma base Event-Driven em que eventos de uso alimentam o ciclo de decisão e aprendizado, mantendo fallback seguro no MVP e preparando evolução incremental para capacidades mais robustas de experimentação e teste A/B.

## Quickstart

Requisitos:

- Python 3.12+

```bash
git clone https://github.com/MariaCarolinass/adaptive-feature-flags.git
cd adaptive-feature-flags
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env
pip install -r requirements.txt
python3 scripts/seed_demo.py
uvicorn app.main:app --reload
```

Teste rapido:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/features
```

## Script de seed demo

O script [`scripts/seed_demo.py`](scripts/seed_demo.py) inicializa a base local com dados de exemplo para facilitar testes manuais do fluxo completo.

Ele faz duas coisas:

- cria features demo (se ainda nao existirem);
- cria eventos sinteticos de usuarios (view, viewed_feature, addtocart e transaction) com `source=seed_demo`.

O script e idempotente: se voce rodar mais de uma vez, ele reaproveita o que ja existe e evita duplicar registros equivalentes.

## Endpoints principais

- `GET /health`
- `POST|GET|PUT|DELETE /features`
- `POST|GET|PUT|DELETE /events`
- `POST /ingest/events`
- `POST /train`
- `POST /train/async`
- `GET /train/jobs/{job_id}`
- `GET /model/status`
- `POST /evaluate`
- `POST /simulate`

## Documentação

A documentação completa do projeto está em [`docs/README.md`](docs/README.md), incluindo:

- visão de produto MVP,
- arquitetura e fluxos,
- referência de API por endpoint,
- decisões técnicas (ADRs),
- implementações críticas de código,
- guia de operação e desenvolvimento,
- roadmap de evolução.

## Testes

```bash
pytest
```
