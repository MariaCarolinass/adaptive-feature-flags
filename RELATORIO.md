# Adaptive Feature Flags: Sistema Inteligente de Gerenciamento de Feature Flags

## Introdução

O projeto **Adaptive Feature Flags** implementa uma API para gerenciamento de *feature flags* com duas estratégias complementares de decisão:

- **Rollout determinístico** por percentual (comportamento previsível e seguro);
- **Decisão assistida por machine learning** por usuário, com fallback automático para rollout quando o modelo não está disponível ou aplicável.

A proposta central é reduzir risco operacional na entrega contínua, automatizando decisões de ativação de funcionalidades com base em sinais de uso reais e métricas operacionais, sem abrir mão de governança e comportamento resiliente.

---

## Identificação

### Integrantes da Equipe

| Nome                           |
| ------------------------------ |
| Maria Carolina de Sousa Soares |

### Link da Apresentação

Slides da apresentação do trabalho:

> Atualizar com o link final da apresentação.

---

## Informações Gerais

### Descrição do Problema

Em ambientes CI/CD, *feature flags* são essenciais para liberar funcionalidades de forma gradual e controlada. Porém, decisões manuais de ativação podem gerar:

- Sobrecarga operacional;
- Dificuldade de priorizar usuários/contextos com maior chance de sucesso;
- Risco de impacto negativo em produção;
- Dificuldade de escalar experimentação com rastreabilidade.

O projeto resolve isso com uma arquitetura orientada a eventos (*event-driven*) e um fluxo de decisão online por usuário que combina ML opcional e fallback determinístico.

### Base de Dados

A base do projeto é composta por **eventos canônicos** de uso, contendo principalmente:

- `user_id`
- `feature_key`
- `event_type`
- `timestamp`
- `properties`

Além de sinais comportamentais, o sistema suporta métricas operacionais opcionais por evento em `properties`:

- `latency_ms`
- `error_rate`
- `cpu_pct`
- `mem_pct`

Esses dados alimentam o pipeline de engenharia de atributos e treino supervisionado.

---

## Arquitetura da Solução

O sistema segue arquitetura em camadas:

- **API (FastAPI)**: contratos HTTP e validações;
- **Domínio**: regras de negócio (treino, avaliação, ingestão, experimentação);
- **Infraestrutura**: SQLite, repositórios, pipeline ML e observabilidade.

Fluxo principal:

1. Eventos entram por `POST /events` ou `POST /ingest/events`;
2. Eventos persistidos são agregados em features por usuário;
3. `POST /train` treina e seleciona o melhor modelo entre candidatos;
4. `POST /evaluate` decide ativação por usuário;
5. Se ML falhar/não estiver pronto, aplica rollout determinístico;
6. Governança e observabilidade são registradas via `/model/runs` e `/metrics`.

---

## Metodologia

### Pipeline de Machine Learning

O treino supervisionado usa features agregadas por usuário (ex.: atividade, recência, distribuição temporal, intensidade de interação). O alvo é binário, derivado de eventos positivos no histórico do usuário.

Modelos avaliados no benchmark interno:

- Logistic Regression
- Random Forest
- Gradient Boosting

O modelo final é selecionado por desempenho em `f1_score` no *holdout*.

### Divisão Treino/Teste

A divisão usa `train_test_split` estratificado, com base de teste mínima de 20% (ajustada para cenários pequenos), garantindo presença de classes em treino e teste.

### Métricas de Avaliação

O processo de treino registra:

- Accuracy
- Precision
- Recall
- F1-Score
- ROC-AUC
- Confusion Matrix

Também calcula `best_threshold_by_f1`, usado no modo de threshold `maximize_f1`.

### Política de Threshold por Feature

Cada feature pode definir sua estratégia de threshold:

- `fixed`: usa valor explícito (`ml_threshold_value`)
- `match_rollout`: aproxima cobertura do percentual de rollout
- `maximize_f1`: usa threshold calibrado no treino

---

## Experimentos e A/B-lite

O projeto implementa uma camada de experimentação gradual (**A/B-lite**) com:

- Cadastro de experimento por feature (`POST /experiments`)
- Alocação determinística de variante A/B por usuário
- Avaliação de resultado (`GET /experiments/{id}/result`)

Regra mínima de parada:

- Exige amostra mínima por variante (`min_samples_per_variant`)
- Exige ganho mínimo (`min_lift`)
- Decisão possível: `continue`, `stop_promote_b`, `stop_keep_a`

Essa abordagem atende ao MVP de experimentação sem depender de um framework A/B completo.

---

## Robustez de Dados

Na ingestão em lote (`POST /ingest/events`), o sistema:

- Valida campos obrigatórios;
- Rejeita timestamp futuro;
- Valida faixas de métricas operacionais (`latency_ms`, `error_rate`, `cpu_pct`, `mem_pct`);
- Continua processando lote parcial;
- Retorna contadores `saved_events` e `rejected`.

Quando há experimento ativo da feature, o evento persistido recebe `ab_variant` automaticamente.

---

## Governança e Observabilidade

### Governança de Modelo

O sistema mantém:

- Status do modelo atual (`GET /model/status`)
- Histórico de execuções de treino (`GET /model/runs`)

Cada execução salva snapshot com:

- versão/modelo escolhido
- métricas
- benchmark de candidatos
- perfil do dataset
- política de threshold/fallback

### Observabilidade Operacional

Endpoint `GET /metrics` expõe snapshot de:

- counters
- gauges
- timings

Permitindo monitorar volume de decisão, rejeições de ingestão e duração de treino.

---

## Endpoints Principais

- `GET /health`
- `POST|GET|PUT|DELETE /features`
- `POST|GET /events`
- `POST /ingest/events`
- `POST /train`
- `GET /model/status`
- `GET /model/runs`
- `POST /evaluate`
- `GET /metrics`
- `POST|GET /experiments`
- `GET /experiments/{id}/result`

---

## Tabela de Aderência (Implementado vs Evolução)

### Implementado

- Decisão híbrida (ML + fallback rollout)
- Benchmark multi-modelo no treino
- Métricas completas de avaliação
- Threshold configurável por feature
- A/B-lite com regra mínima de parada
- Validação robusta de ingestão
- Governança de treino com histórico
- Observabilidade por endpoint de métricas

### Evolução Futura

- Significância estatística completa para experimentação (intervalos de confiança, p-valor)
- Dashboard visual dedicado para métricas e experimentos
- Aprendizado contínuo/automático com janelas temporais e detecção de drift avançada

---

## Conclusão

O projeto Adaptive Feature Flags evoluiu de uma proposta conceitual para uma implementação prática de tomada de decisão adaptativa, conciliando segurança operacional e inteligência incremental.

A arquitetura orientada a eventos, o benchmark de modelos, o controle de threshold por feature, a camada A/B-lite e os mecanismos de governança/observabilidade tornam a solução aderente a cenários reais de engenharia de software moderna.

Como próximos passos, a expansão natural é fortalecer a análise estatística de experimentos, ampliar visualização operacional e evoluir mecanismos de monitoramento de drift e re-treino contínuo.
