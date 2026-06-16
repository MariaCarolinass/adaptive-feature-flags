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

Abra a interface web:

```text
http://localhost:8000/
```

A tela inicial carrega o painel do produto com navegação lateral para resumo, insights, regras, avaliação, atividades e treinos. A interface usa a própria API para listar regras, carregar eventos, avaliar usuários, registrar atividades e consultar o estado do modelo.

Acesse a documentação interativa da API:

```text
http://localhost:8000/docs
http://localhost:8000/redoc
http://localhost:8000/openapi.json
```

Essas páginas ficam disponíveis quando `ENABLE_DOCS=true` no `.env`.

Teste rápido de disponibilidade:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/features
```

## Como testar o projeto

Depois de instalar e subir a API, você pode escolher **1 de 2 caminhos** para popular dados:

### Opção 1: Seed demo (mais rápido)

O script [`scripts/seed_demo.py`](scripts/seed_demo.py) inicializa a base local com dados de exemplo para facilitar testes manuais do fluxo completo. Sem argumentos, ele importa todos os catálogos JSON do diretório [`dataset/`](dataset/), sincroniza as features demo e gera uma trilha de eventos correlacionados por usuário, com jornadas que fazem sentido no dashboard.

```bash
python3 scripts/seed_demo.py
```

Para importar só um catálogo:

```bash
python3 scripts/seed_demo.py --catalog dataset/seed_demo_checkout_focus.json
python3 scripts/seed_demo.py --catalog dataset/seed_demo_growth_focus.json
python3 scripts/seed_demo.py --catalog dataset/seed_demo_activation_focus.json
python3 scripts/seed_demo.py --catalog dataset/seed_demo_retention_focus.json
python3 scripts/seed_demo.py --catalog dataset/seed_demo_auth_focus.json
```

O script é idempotente: rodar mais de uma vez não duplica registros equivalentes. Os eventos são distribuídos ao longo de vários dias e incluem fluxos como `view -> checkout_upsell_shown -> checkout_upsell_clicked/purchase_completed` ou `view -> onboarding_step_shown -> onboarding_completed`.
Cada catálogo gera 50 usuários sintéticos com distribuição por perfil, o que deixa a base mais útil para treino e mais crível na UI.

### Taxonomia de eventos

O projeto separa os eventos em quatro grupos para transformar telemetria bruta em sinais de produto:

- `VIEW_EVENT_TYPES`: exposição inicial. Exemplo: `view`, `checkout_upsell_shown`, `onboarding_step_shown`.
- `INTERMEDIATE_POSITIVE_EVENT_TYPES`: sinais de interesse no meio do funil. Exemplo: `checkout_upsell_clicked`, `pricing_details_opened`, `hero_cta_clicked`.
- `TERMINAL_POSITIVE_EVENT_TYPES`: conversão final. Exemplo: `transaction`, `purchase_completed`, `subscription_upgraded`.
- `POSITIVE_EVENT_TYPES`: união dos sinais que contam como sucesso/valor para o treino e para a avaliação.

O fluxo do ML usa essa taxonomia para construir agregados por usuário, treinar o modelo e decidir se uma feature deve ficar ligada com base no score do modelo ou no rollout determinístico. O detalhamento completo está em [`docs/implementation/ml-decision-flow-in-depth.md`](docs/implementation/ml-decision-flow-in-depth.md).

### Opção 2: Importação CSV

O importador oficial é o [`scripts/import_events_csv.py`](scripts/import_events_csv.py). Ele importa eventos de CSV para o schema canônico de eventos da API.
O projeto pode ser testado com qualquer arquivo CSV compatível: use `ecommerce_dataset` se o arquivo seguir o contrato do dataset e-commerce, ou `generic` para qualquer outro layout com mapeamento de colunas.

Modos suportados:

- `--adapter ecommerce_dataset`: para CSV no formato de dataset e-commerce (`timestamp`, `visitorid`, `event`, `itemid`).
- `--adapter generic`: para CSV customizado com mapeamento via `--mapping-json`.

Detalhes dos adapters e exemplos completos: [`docs/operations/csv-import-adapters.md`](docs/operations/csv-import-adapters.md)

Exemplos:

```bash
python3 scripts/import_events_csv.py \
  --adapter ecommerce_dataset \
  --csv ./seu_arquivo.csv \
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

- `GET /` - interface web
- `GET /docs` - Swagger UI, quando `ENABLE_DOCS=true`
- `GET /redoc` - ReDoc, quando `ENABLE_DOCS=true`
- `GET /openapi.json` - schema OpenAPI, quando `ENABLE_DOCS=true`
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
