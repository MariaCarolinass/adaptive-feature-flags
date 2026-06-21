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

- Testes: `pytest`
- Healthcheck: `curl http://localhost:8000/health`
- Features: `curl http://localhost:8000/features`
- Treino: `curl -X POST http://localhost:8000/train`

## Scripts do projeto

### `scripts/seed_demo.py`

- Importa catálogos JSON do diretório [`dataset/`](../../dataset/).
- Aceita `--catalog` para importar apenas um catálogo.
- Catálogos prontos: `seed_demo_checkout_focus.json`, `seed_demo_growth_focus.json`, `seed_demo_activation_focus.json`, `seed_demo_retention_focus.json` e `seed_demo_auth_focus.json`.
- Os eventos seguem a taxonomia descrita em [`docs/implementation/ml-decision-flow-in-depth.md`](../implementation/ml-decision-flow-in-depth.md).

Comando:

```bash
python3 scripts/seed_demo.py
```

Efeito:

- sincroniza as features demo com o catálogo esperado;
- gera 50 usuários sintéticos por catálogo;
- cria eventos sintéticos correlacionados por usuário e por jornada;
- distribui os eventos ao longo de vários dias para deixar o dashboard mais crível;
- é idempotente (evita duplicação equivalente).

### `scripts/import_events_csv.py`

- Importa eventos de CSV para o schema canônico.
- No modo `generic`, basta mapear as colunas canônicas.
- No modo `ecommerce_dataset`, o CSV segue o contrato do dataset e-commerce.

Comando (dataset e-commerce):

```bash
python3 scripts/import_events_csv.py \
  --adapter ecommerce_dataset \
  --csv ./seu_arquivo.csv \
  --feature-key-mode item \
  --limit 10000
```

Comando (CSV customizado):

```bash
python3 scripts/import_events_csv.py \
  --adapter generic \
  --csv ./seu_arquivo.csv \
  --source web_app \
  --mapping-json '{"user_id":"uid","feature_key":"feature","event_type":"event_name","timestamp":"ts"}'
```

### `scripts/build_user_features.py`

- Gera features por usuário a partir da tabela `events`.

Comando:

```bash
python3 scripts/build_user_features.py --output-table user_features
```

- `--dry-run`: processa sem gravar na base.

### `scripts/test_model.py`

- Compara o modelo treinado com o baseline de rollout determinístico.

Comando:

```bash
python3 scripts/test_model.py \
  --artifact-path storage/models/v1.joblib \
  --rollout-percentage 10
```

- Saída principal: acurácia, taxa positiva de machine learning versus rollout e métricas de negócio (`Machine Learning Engagement`, `Rollout Engagement`, `Uplift`).

## Variáveis de ambiente

- `DATABASE_URL`
- `MODELS_DIR`
- `ENABLE_DOCS`
- `AUTH_ENABLED`
- `AUTH_JWT_SECRET`
- `AUTH_ISSUER_KEY`
- `AUTH_TOKEN_EXPIRE_MINUTES`
- `AUTH_EXEMPT_PATHS`
- `LOG_LEVEL`
- `POSITIVE_EVENT_TYPES`
- `VIEW_EVENT_TYPES`
- `INTERMEDIATE_POSITIVE_EVENT_TYPES`
- `TERMINAL_POSITIVE_EVENT_TYPES`

## Autenticação local

Exemplo no `.env`:

```env
AUTH_ENABLED=true
AUTH_JWT_SECRET=minha-chave-jwt-local
AUTH_ISSUER_KEY=minha-chave-emissora
AUTH_TOKEN_EXPIRE_MINUTES=60
```

Emitir token:

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"issuer_key":"minha-chave-emissora","subject":"dev-local","expires_minutes":60}'
```

Exemplo de chamada autenticada:

```bash
curl -H "Authorization: Bearer <token-jwt>" http://localhost:8000/features
```

## Checklist antes de PR

1. Executar `pytest`.
2. Validar fluxo básico: `features -> events/ingest -> train -> evaluate`.
3. Revisar impacto em fallback (`decision_source`).
4. Atualizar docs em `docs/` quando mudar regra de negócio, endpoint ou comportamento de machine learning.
