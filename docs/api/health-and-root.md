# Root e Health

## `GET /`

Retorna uma mensagem simples de identificação da API.

Exemplo de resposta:

```json
{
  "message": "Adaptive Feature Flags"
}
```

## `GET /health`

Endpoint de healthcheck para monitoramento básico de disponibilidade.

Exemplo de resposta:

```json
{
  "status": "ok"
}
```

## `GET /metrics`

Snapshot das métricas de processo coletadas em memória (counters, gauges e timings).

Exemplo de resposta:

```json
{
  "counters": {
    "evaluation.count": 120,
    "ingest.saved.count": 5000
  },
  "gauges": {
    "ingest.rejection_rate": 0.02
  },
  "timings_ms": {
    "training.duration_ms": 4280
  }
}
```
