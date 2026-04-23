# Smart Feature Flags API

Smart Feature Flags é uma API de **feature flags** construída com **Python** + **FastAPI**, preparada para evoluir decisões de liberação com suporte de **aprendizado de máquina (ML)**.

## Quickstart

Requisitos:

- Python 3.12+

Por padrão, a aplicação usa **SQLite** em `./db.sqlite3` (as tabelas são criadas automaticamente ao iniciar).

```bash
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Documentação interativa:

- `/docs`
- `/redoc`

Rodar testes:

```bash
pytest
```

Configuração do banco (opcional):

```bash
export DATABASE_URL="sqlite:///./db.sqlite3"
```

Configurações adicionais (segurança/execução):

```bash
export ENVIRONMENT=development
export LOG_LEVEL=INFO
export MODELS_DIR="storage/models"
export POSITIVE_EVENT_TYPES='["addtocart","transaction","used_feature"]'
export VIEW_EVENT_TYPES='["view","viewed_feature"]'
export INTERMEDIATE_POSITIVE_EVENT_TYPES='["addtocart"]'
export TERMINAL_POSITIVE_EVENT_TYPES='["transaction"]'
export ENABLE_DOCS=true
export TRUSTED_HOSTS='["localhost","127.0.0.1","testserver"]'
export CORS_ALLOWED_ORIGINS='["http://localhost:3000"]'
```

## Atualizações recentes da API

- IDs de `features` e `events` usam **inteiro autoincrement** (não UUID).
- `POST /train` treina o modelo com eventos persistidos e salva metadados em `model_metadata`, incluindo `artifact_path`.
- `POST /evaluate` usa score real do artefato quando o modelo está `ready`; se houver falha no score, faz fallback para rollout determinístico.
- Tipos de evento usados pelo pipeline de ML são configuráveis por ambiente:
  - `POSITIVE_EVENT_TYPES`
  - `VIEW_EVENT_TYPES`
  - `INTERMEDIATE_POSITIVE_EVENT_TYPES`
  - `TERMINAL_POSITIVE_EVENT_TYPES`

## Arquitetura

O projeto segue uma **Arquitetura em Camadas** (Layered Architecture), inspirada em **DDD “lite”**:

- **Domain (`app/domain/`)**
  - **Entidades** (`entities/`): estruturas de dados do domínio (dataclasses).
  - **Contratos** (`repositories/`): interfaces de repositório (o domínio depende de abstrações).
  - **Services** (`services/`): regras de negócio e orquestração (sem FastAPI/SQLAlchemy).

- **Infrastructure (`app/infrastructure/`)**
  - **Persistência** (`db/models.py`, `db/db.py`): modelos SQLAlchemy e sessão/engine.
  - **Repositórios concretos** (`repositories/`): implementação SQLite dos contratos do domínio.

- **API (`app/api/` + `app/schemas/`)**
  - **Rotas** FastAPI (HTTP) e **schemas** Pydantic (I/O).
  - Rotas chamam services; services chamam repositórios via contratos.

### Fluxo do CRUD (padrão do projeto)

Quando for adicionar/alterar operações de CRUD, a regra é manter as camadas alinhadas:

1. **Contrato** no domínio (`app/domain/repositories/*`)
2. **Regra/validação** no service (`app/domain/services/*`)
3. **Implementação** no repositório SQLite (`app/infrastructure/repositories/*`)
4. **Exposição HTTP** na rota (`app/api/v1/routes/*`)

Documentacao dedicada do fluxo de decisao:

- `docs/rollout-ml.md` (como rollout e ML interagem no `/evaluate`, com fallback e operacao)

## Endpoints principais

- **Sistema**: `GET /`, `GET /health`
- **Features**: `POST/GET/GET by id/PUT/DELETE` em `/features`
- **Events**: `POST/GET/GET by id/PUT/DELETE` em `/events` (com filtros via query params em `GET /events`)
- **Evaluation**: `POST /evaluate`
- **Training**: `POST /train`, `POST /train/async`, `GET /train/jobs/{job_id}`, `GET /model/status`
- **Simulation**: `POST /simulate` (importa CSV por URL ou upload de arquivo)

Observação de contrato:

- Parâmetros `{feature_id}` e `{event_id}` são inteiros.

## Importação de dataset (Retailrocket)

Use o script abaixo para popular a tabela `events`:

```bash
python scripts/import_retailrocket.py --csv dataset-ml/retailrocket/events.csv
```

Opções úteis:

```bash
python scripts/import_retailrocket.py --csv dataset-ml/retailrocket/events.csv --limit 10000
python scripts/import_retailrocket.py --csv dataset-ml/retailrocket/events.csv --feature-key-mode single
python scripts/import_retailrocket.py --csv dataset-ml/retailrocket/events.csv --sync-features --feature-rollout-percentage 10 --feature-ml-enabled
python scripts/import_retailrocket.py --csv dataset-ml/retailrocket/events.csv --chunk-size 200000 --batch-size 10000 --sync-features
```

Se precisar resetar o banco local durante os testes, recrie o arquivo SQLite:

```bash
rm -f db.sqlite3
python -c "from app.infrastructure.db.db import init_db; init_db(); print('banco recriado')"
```

## Pipeline recomendado (Retailrocket -> treino -> avaliação)

1. Importar eventos e sincronizar `features` automaticamente:

```bash
python scripts/import_retailrocket.py --csv dataset-ml/retailrocket/events.csv --sync-features
```

2. (Opcional) Gerar tabela derivada `user_features` para análise offline:

```bash
python scripts/build_features.py --output-table user_features --if-exists replace
```

3. Treinar modelo:

```bash
curl -X POST "http://localhost:8000/train"
```

4. Avaliar um usuário em uma feature importada:

```bash
curl -X POST "http://localhost:8000/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"feature_key":"item_355908","user":{"user_id":"257597"}}'
```

5. (Opcional) Validar qualidade do modelo offline, comparando ML vs rollout:

```bash
python scripts/test_model.py \
  --artifact-path storage/models/v1.joblib \
  --rollout-percentage 10 \
  --ml-threshold-mode match_rollout
```

### Sobre `build_features.py`

- Por padrão salva em `user_features`.
- Use `--dry-run` para somente calcular sem salvar.
- Use `--if-exists` (`replace|append|fail`) para controlar escrita da tabela.

### Sobre `test_model.py`

- Compara o desempenho do modelo com o rollout determinístico.
- Usa holdout estratificado e reporta acurácia, taxa positiva, engagement e uplift.
- Modos de threshold:
  - `match_rollout`: ajusta threshold para cobertura semelhante ao rollout.
  - `fixed`: usa `--fixed-threshold` (0.0 a 1.0).

## Treino assíncrono (exemplo)

Iniciar job:

```bash
curl -X POST "http://localhost:8000/train/async"
```

Consultar status do job (substitua `{job_id}`):

```bash
curl "http://localhost:8000/train/jobs/{job_id}"
```

Consultar status atual do modelo:

```bash
curl "http://localhost:8000/model/status"
```

## Simulação (exemplos)

Importar dataset por URL:

```bash
curl -X POST "http://localhost:8000/simulate" \
  -F "csv_url=https://raw.githubusercontent.com/retailrocket/ecommerce-dataset/master/events.csv" \
  -F "feature_key_mode=item" \
  -F "sync_features=true" \
  -F "feature_rollout_percentage=10" \
  -F "feature_ml_enabled=true"
```

Importar dataset por upload de arquivo CSV:

```bash
curl -X POST "http://localhost:8000/simulate" \
  -F "csv_file=@dataset-ml/retailrocket/events.csv" \
  -F "feature_key_mode=item" \
  -F "limit=10000" \
  -F "chunk_size=200000" \
  -F "batch_size=10000" \
  -F "sync_features=true"
```

Regras da rota:

- Envie **exatamente uma** fonte: `csv_url` ou `csv_file`.
- Colunas obrigatórias do CSV: `timestamp`, `visitorid`, `event`, `itemid`.
- `feature_key_mode`:
  - `item`: gera `feature_key=item_<itemid>`
  - `single`: usa `feature_key=retailrocket_import`

## Segurança da API

- **Trusted Host** com allowlist configurável (`TRUSTED_HOSTS`).
- **CORS restritivo** com allowlist configurável (`CORS_ALLOWED_ORIGINS`).
- **Headers de segurança** em todas as respostas:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: no-referrer`
  - `Permissions-Policy` restritiva
- **Tratamento global de exceções** retorna payload genérico em erro inesperado:
  - `{"detail": "Internal server error."}`
- **Docs OpenAPI desabilitáveis** em ambientes sensíveis (`ENABLE_DOCS=false`).

## Como citar

Este repositório inclui um arquivo `CITATION.cff` compatível com o GitHub ("Cite this repository").
