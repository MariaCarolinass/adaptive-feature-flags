# Guia de Módulos Ativos e Suporte

Este guia explica o papel dos módulos que hoje parecem "secundários", mas são importantes para operação, ingestão e uso externo.

## `app/core/event_types.py`

Papel:

- Centraliza a normalização dos tipos de evento usados pelo pipeline de ML.

Como funciona:

- Lê listas do `settings` (`POSITIVE_EVENT_TYPES`, `VIEW_EVENT_TYPES`, etc).
- Remove valores vazios e espaços.
- Expõe `frozenset` para uso consistente.

Quem usa:

- `app/infrastructure/ml/feature_builder.py`
- `app/domain/services/training_service.py`

Impacto:

- Alterar esses conjuntos muda a definição de "evento positivo" e o `target` do treino.

## `app/infrastructure/integrations/`

Papel:

- Converter CSV externo para evento canônico da aplicação.

Arquivos:

- `base.py`: contratos (`EventCSVAdapter`) e configuração (`CSVAdapterConfig`).
- `csv_adapter.py`: adapter genérico baseado em mapeamento.
- `ecommerce_adapter.py`: adapter especializado para o formato do dataset e-commerce.

Quem usa:

- `scripts/import_events_csv.py`

Impacto:

- Mudanças aqui afetam importação de dados históricos e qualidade do dataset de treino.

## `app/infrastructure/observability/`

Papel:

- Interface de métricas da aplicação e implementação default local.

Arquivos:

- `metrics.py`: `MetricsSink`, `NoopMetricsSink`, `InMemoryLoggingMetricsSink`.

Como funciona hoje:

- Serviços emitem métricas sem acoplamento a ferramenta específica.
- Sink default grava em memória e loga no logger.

Quem usa:

- `TrainingService`
- `EvaluationService`
- Injeção em `app/dependencies.py` via `metrics_sink`.

Impacto:

- Permite trocar para Prometheus/Datadog/OpenTelemetry sem reescrever regras de negócio.

## `sdk/` e `examples/`

Papel:

- Cliente Python e exemplos de integração externa com a API.

Arquivos:

- `sdk/adaptiveflags/client.py`: cliente HTTP simples (`evaluate`, `track`, `train`, `model_status`).
- `examples/*.py`: uso prático em app externa e fluxo de cliente.

Status:

- Não fazem parte do runtime da API.
- São importantes para adoção, testes manuais e referência de integração.

Impacto:

- Mudanças de contrato da API devem refletir nesses arquivos para evitar exemplos quebrados.

