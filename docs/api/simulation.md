# Simulation

## `POST /simulate`

Importa dados de CSV para simulação de fluxo ponta a ponta (eventos -> treino -> avaliação).

Formato: `multipart/form-data`.

Base usada nos exemplos: https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset/data

Regras:

- Enviar exatamente uma fonte: `csv_url` ou `csv_file`.
- CSV esperado com colunas `timestamp`, `visitorid`, `event`, `itemid`.

Parâmetros principais:

- `feature_key_mode`: `item` ou `single`
- `limit`
- `chunk_size`
- `batch_size`
- `sync_features`
- `feature_rollout_percentage`
- `feature_ml_enabled`

Exemplo com URL:

```bash
curl -X POST http://localhost:8000/simulate \
  -F "csv_url=https://example.com/events.csv" \
  -F "feature_key_mode=item" \
  -F "sync_features=true"
```

Exemplo com upload:

```bash
curl -X POST http://localhost:8000/simulate \
  -F "csv_file=@dataset/events.csv" \
  -F "feature_key_mode=single" \
  -F "limit=10000"
```
