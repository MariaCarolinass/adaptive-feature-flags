# Training e Model Status

## `POST /train`

Executa treino síncrono do modelo com base nos eventos persistidos.

Exemplo de resposta:

```json
{
  "status": "ready",
  "model_name": "random_forest",
  "model_version": "v1",
  "artifact_path": "storage/models/v1.joblib",
  "trained_at": "2026-05-23T12:10:00Z",
  "metrics": {
    "accuracy": 0.82,
    "f1_score": 0.79
  },
  "process": {
    "total_events": 100000,
    "unique_users": 30000,
    "positive_events": 12000,
    "duration_ms": 4200,
    "feature_columns": [
      "unique_features",
      "active_days"
    ]
  }
}
```

## `POST /train/async`

Inicia treino assíncrono e retorna `job_id`.

Response `202`:

```json
{
  "job_id": "7f01a2a10b1b4f7b96f8f6f8c4d9a123",
  "status": "queued",
  "submitted_at": "2026-05-23T12:12:00Z"
}
```

## `GET /train/jobs/{job_id}`

Consulta status de job assíncrono.

Status esperados:

- `queued`
- `running`
- `succeeded`
- `failed`

## `GET /model/status`

Retorna estado atual do último modelo treinado.

Exemplo:

```json
{
  "status": "ready",
  "model_name": "random_forest",
  "model_version": "v1",
  "trained_at": "2026-05-23T12:10:00Z",
  "metrics": {
    "accuracy": 0.82,
    "f1_score": 0.79
  }
}
```

## Fluxo dos endpoints de treino

```mermaid
flowchart LR
    A[POST /train/async] --> B[job_id]
    B --> C[GET /train/jobs/{job_id}]
    C --> D{status}
    D --> E[queued]
    D --> F[running]
    D --> G[succeeded ou failed]
    H[POST /train] --> I[treino síncrono]
    I --> J[GET /model/status]
```
