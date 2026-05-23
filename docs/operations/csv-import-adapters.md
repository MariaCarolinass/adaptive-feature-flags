# Importacao CSV: Adapters

Este guia explica a diferenca entre os adapters do script `scripts/import_events_csv.py`, com foco no modo `generic`.

## Visao geral

O script suporta dois adapters:

- `ecommerce_dataset`: formato fixo do dataset e-commerce.
- `generic`: formato customizado via mapeamento.

## Adapter `ecommerce_dataset`

Use quando o CSV segue este contrato:

- `timestamp` (epoch em milissegundos)
- `visitorid`
- `event`
- `itemid`
- `transactionid` (opcional)

Comportamento:

- `user_id <- visitorid`
- `event_type <- event`
- `timestamp <- timestamp` (parse como ms UTC)
- `feature_key`:
  - `item`: `item_<itemid>`
  - `single`: `dataset_import`

Exemplo:

```bash
python3 scripts/import_events_csv.py \
  --adapter ecommerce_dataset \
  --csv dataset/events.csv \
  --feature-key-mode item \
  --limit 10000
```

## Adapter `generic`

Use quando o CSV nao tem os mesmos nomes de coluna do formato acima.

### Requisitos obrigatorios

No `--mapping-json`, voce precisa mapear estes campos canônicos:

- `user_id`
- `feature_key`
- `event_type`
- `timestamp`

Cada valor do mapeamento e o nome da coluna no seu CSV.

Exemplo de mapeamento:

```json
{
  "user_id": "uid",
  "feature_key": "flag",
  "event_type": "action",
  "timestamp": "ts"
}
```

Comando:

```bash
python3 scripts/import_events_csv.py \
  --adapter generic \
  --csv ./events.csv \
  --source web_app \
  --mapping-json '{"user_id":"uid","feature_key":"flag","event_type":"action","timestamp":"ts"}'
```

### Regras importantes do `generic`

- `--source` e obrigatorio (valor salvo em `event.source`).
- `--mapping-json` e obrigatorio.
- Se uma coluna mapeada nao existir ou vier nula, a linha e ignorada.
- `timestamp` e parseado por `pandas.to_datetime(..., utc=True)`.

## Como escolher

- Use `ecommerce_dataset` se seu CSV ja e desse formato.
- Use `generic` para qualquer layout customizado.
