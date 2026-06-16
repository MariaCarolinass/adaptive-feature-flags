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

## Scripts do projeto

### `scripts/seed_demo.py`

Uso: popular ambiente local rapidamente com dados sintéticos.

Sem argumentos, o script importa todos os catálogos JSON do diretório [`dataset/`](../../dataset/) para manter os dados fora do código.
Também aceita `--catalog` para apontar um JSON específico quando você quiser importar só um catálogo.
Catálogos prontos: [`dataset/seed_demo_checkout_focus.json`](../../dataset/seed_demo_checkout_focus.json), [`dataset/seed_demo_growth_focus.json`](../../dataset/seed_demo_growth_focus.json), [`dataset/seed_demo_activation_focus.json`](../../dataset/seed_demo_activation_focus.json), [`dataset/seed_demo_retention_focus.json`](../../dataset/seed_demo_retention_focus.json) e [`dataset/seed_demo_auth_focus.json`](../../dataset/seed_demo_auth_focus.json).
Os catálogos usam eventos específicos do contexto, por exemplo `checkout_upsell_shown`, `checkout_upsell_clicked`, `purchase_completed`, `onboarding_step_shown`, `onboarding_completed` e `weekly_digest_opened`.
Esses eventos seguem a taxonomia descrita em [`docs/implementation/ml-decision-flow-in-depth.md`](../implementation/ml-decision-flow-in-depth.md), onde `VIEW_EVENT_TYPES`, `INTERMEDIATE_POSITIVE_EVENT_TYPES`, `TERMINAL_POSITIVE_EVENT_TYPES` e `POSITIVE_EVENT_TYPES` são explicados no contexto do treino e da decisão online.

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

Uso: importar eventos de CSV para o schema canônico de eventos.
O projeto pode ser testado com qualquer arquivo CSV compatível: no modo `generic`, basta mapear as colunas canônicas; no modo `ecommerce_dataset`, o CSV precisa seguir o contrato do dataset e-commerce.

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

Uso: gerar features por usuário a partir da tabela `events` e gravar em tabela SQL.

Comando:

```bash
python3 scripts/build_user_features.py --output-table user_features
```

Opção útil:

- `--dry-run`: processa sem gravar na base.

### `scripts/test_model.py`

Uso: comparar o modelo treinado com o baseline de rollout determinístico.

Comando:

```bash
python3 scripts/test_model.py \
  --artifact-path storage/models/v1.joblib \
  --rollout-percentage 10
```

Saída principal:

- acurácia e taxa positiva de ML vs rollout;
- métricas de negócio (`ML Engagement`, `Rollout Engagement`, `Uplift`).

## Variáveis de ambiente relevantes

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

## Ativando autenticação local

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
