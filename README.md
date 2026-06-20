# Adaptive Feature Flags

Adaptive Feature Flags é uma API de feature flags com rollout determinístico e suporte opcional a machine learning para decisão por usuário. O sistema usa uma base Event-Driven em que eventos de uso alimentam o ciclo de decisão e aprendizado, mantendo fallback seguro no MVP e preparando evolução incremental para capacidades mais robustas de experimentação e teste A/B.

<img src="ui/dashboard.gif" alt="Dashboard demo" width="900"/>

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

A tela inicial carrega o painel do produto com navegação lateral para resumo, insights, regras, avaliação, atividades, testes e modelo.

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

## Dados de teste

O caminho mais rápido para popular a base local é o seed demo:

```bash
python3 scripts/seed_demo.py
```

Ele sincroniza as features demo, cria eventos coerentes por usuário e deixa a UI útil para navegação, treino e avaliação. A taxonomia de eventos usada pelo treino está descrita em [`docs/implementation/ml-decision-flow-in-depth.md`](docs/implementation/ml-decision-flow-in-depth.md).

## Avaliar modelo vs rollout

O script [`scripts/test_model.py`](scripts/test_model.py) compara o desempenho do modelo treinado com o baseline de rollout determinístico.

Exemplo:

```bash
python3 scripts/test_model.py \
  --artifact-path storage/models/v1.joblib \
  --rollout-percentage 10
```

## Autenticação da API (JWT)

Ative autenticação no `.env`:

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
- `GET /health`
- `POST|GET|PUT|DELETE /activities`
- `POST|GET|PUT|DELETE /features`
- `POST|GET /events`
- `POST /train`
- `POST /evaluate`
- `POST|GET /experiments`

Os contratos completos ficam em [`docs/README.md`](docs/README.md).

## Testes

```bash
pytest
```
