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
```

Inicie a API:

```bash
uvicorn app.main:app --reload
```

Teste rápido de disponibilidade:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/features
```

## Como testar o projeto

Depois de instalar e subir a API, você pode escolher **1 de 2 caminhos** para popular dados:

### Opção 1: Seed demo (mais rápido)

O script [`scripts/seed_demo.py`](scripts/seed_demo.py) inicializa a base local com dados de exemplo para facilitar testes manuais do fluxo completo.

```bash
python3 scripts/seed_demo.py
```

O script é idempotente: rodar mais de uma vez não duplica registros equivalentes.

### Opção 2: Importação CSV

O importador oficial é o [`scripts/import_events_csv.py`](scripts/import_events_csv.py). Ele importa eventos de CSV para o schema canônico de eventos da API.

Modos suportados:

- `--adapter ecommerce_dataset`: para CSV no formato de dataset e-commerce (`timestamp`, `visitorid`, `event`, `itemid`).
- `--adapter generic`: para CSV customizado com mapeamento via `--mapping-json`.

Detalhes dos adapters e exemplos completos: [`docs/operations/csv-import-adapters.md`](docs/operations/csv-import-adapters.md)

Exemplos:

```bash
python3 scripts/import_events_csv.py \
  --adapter ecommerce_dataset \
  --csv dataset/events.csv \
  --feature-key-mode item \
  --limit 10000
```

Se seu CSV for customizado, use `--adapter generic` com `--mapping-json`.

## Avaliar modelo vs rollout

O script [`scripts/test_model.py`](scripts/test_model.py) compara o desempenho do modelo treinado com o baseline de rollout determinístico.

Exemplo:

```bash
python3 scripts/test_model.py \
  --artifact-path storage/models/v1.joblib \
  --rollout-percentage 10
```

## Autenticação da API (JWT)

Para proteger a API, ative autenticação no `.env`:

```env
AUTH_ENABLED=true
AUTH_JWT_SECRET=minha-chave-jwt-local
AUTH_ISSUER_KEY=minha-chave-emissora
AUTH_TOKEN_EXPIRE_MINUTES=60
```

Gerar token:

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"issuer_key":"minha-chave-emissora","subject":"dev-local","expires_minutes":60}'
```

Usar token:

```bash
curl -H "Authorization: Bearer <token-jwt>" http://localhost:8000/features
```

## Endpoints principais

- `GET /health`
- `POST|GET|PUT|DELETE /features`
- `POST|GET /events`
- `POST /ingest/events`
- `POST /train`
- `GET /model/status`
- `GET /model/runs`
- `POST /evaluate`
- `GET /metrics`
- `POST|GET /experiments`
- `GET /experiments/{id}/result`

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
