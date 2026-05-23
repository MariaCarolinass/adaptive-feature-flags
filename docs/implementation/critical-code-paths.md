# Critical Code Paths

Este documento mapeia implementações importantes para manutenção e evolução segura.

## 1) Decisão online de feature (`/evaluate`)

- Entrada HTTP: `app/api/v1/routes/evaluate.py`
- Regra central: `app/domain/services/evaluation_service.py`
- Dependencias: `feature_service`, `event_service`, `training_service`, `predictor`

Pontos de cuidado:

- Não quebrar fallback para `decision_source="rollout"`.
- Garantir baixa latência.
- Evitar side effects não deterministas no caminho online.

## 2) Treino de modelo

- Orquestração: `app/domain/services/training_service.py`
- Job async: `app/domain/services/training_job_service.py`
- Treinamento: `app/infrastructure/ml/trainer.py`
- Features de machine learning: `app/infrastructure/ml/feature_builder.py`
- Persistência do artefato: `app/infrastructure/ml/serializer.py`

Pontos de cuidado:

- Compatibilidade entre colunas esperadas no treino e inferência.
- Persistência correta de metadados (`model_version`, `artifact_path`, `status`).

## 3) Ingestão e normalização de eventos

- API de ingestão: `app/api/v1/routes/ingest.py`
- Service: `app/domain/services/ingest_service.py`
- Entidade e repositório: `app/domain/entities/event.py`, `app/infrastructure/repositories/sqlite_event_repository.py`

Pontos de cuidado:

- Idempotência e validação de payload em lote.
- Mapeamento consistente de `event_type` para pipeline de treino.

## 4) CRUD de features

- Rotas: `app/api/v1/routes/features.py`
- Service: `app/domain/services/feature_service.py`
- Repositorio: `app/infrastructure/repositories/sqlite_feature_repository.py`

Pontos de cuidado:

- Não permitir estados inconsistentes (`enabled`, `ml_enabled`, `rollout_percentage`).
- Manter contrato de repositório alinhado com testes.

## 5) Recomendação de rollout da feature

- Rota: `app/api/v1/routes/features.py` (`/features/{feature_key}/recommendation`)
- Service: `app/domain/services/recommendation_service.py`

Pontos de cuidado:

- Separar claramente recomendação estratégica de decisão online.
- Não aplicar alteração automática de rollout sem camada explícita de aprovação.
