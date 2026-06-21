# Dataset Seed: Como os JSONs viram dados sintéticos

Este documento explica como os arquivos JSON em `dataset/` entram no sistema, quais variáveis eles usam e como o seed gera dados sintéticos consistentes.

## 1) Estrutura dos JSON em `dataset/`

Os catálogos de seed são lidos por [`scripts/seed_demo.py`](../../scripts/seed_demo.py).
Cada JSON representa um catálogo temático e traz:

- `seed_source`: origem lógica do catálogo;
- `seed_version`: versão do catálogo;
- `user_prefix`: prefixo usado para gerar usuários sintéticos;
- `seed_anchor`: data base do seed;
- `seed_window_days`: janela temporal do catálogo;
- `random_seed`: semente determinística do gerador;
- `features`: regras que o catálogo deve garantir;
- `activities`: atividades canônicas do catálogo;
- `profiles`: perfis de usuários sintéticos;
- `journeys`: mapeamento de jornada por feature.

### Exemplo de papel de cada campo

- `seed_source` ajuda a identificar de onde o catálogo veio;
- `seed_version` permite evoluir o catálogo sem ambiguidade;
- `user_prefix` evita colisão entre usuários de catálogos diferentes;
- `seed_anchor` define o início temporal dos eventos;
- `seed_window_days` controla a dispersão temporal do seed;
- `random_seed` garante repetibilidade;
- `features` sincroniza o seed com a tabela de features;
- `activities` sincroniza o catálogo com a tabela de atividades;
- `profiles` controla o comportamento dos usuários;
- `journeys` define quais eventos compõem cada jornada de produto.

## 2) Como o seed é inserido no sistema

O fluxo do seed é:

1. `init_db()` garante a base local.
2. O catálogo JSON é carregado.
3. `seed_activities()` sincroniza atividades.
4. `seed_features()` sincroniza features.
5. `seed_events()` gera e grava eventos.

### Sincronização de atividades

Se o catálogo já traz `activities`, elas são usadas diretamente.

Se não trouxer, o script cria atividades padrão a partir de `journeys`:

- pega `exposure_event`, `positive_event` e `conversion_event`;
- remove duplicados;
- cria um fallback para `view` se ele ainda não existir.

Cada atividade criada usa:

- `key`
- `name`
- `description`
- `enabled`

### Sincronização de features

As features do JSON são comparadas com a tabela `features` por `key`.

Se a feature não existir:

- o seed cria a feature.

Se a feature já existir e mudou:

- o seed atualiza o registro.

Campos sincronizados:

- `name`
- `key`
- `description`
- `enabled`
- `rollout_percentage`
- `ml_enabled`
- `ml_threshold_mode`
- `ml_threshold_value`

## 3) Como os eventos sintéticos são gerados

O seed gera eventos por usuário, perfil e jornada.

### Variáveis usadas na geração

- `USERS_PER_CATALOG = 50`: usuários criados por catálogo.
- `random_seed`: semente do gerador pseudoaleatório.
- `seed_window_days`: janela temporal total.
- `profile.positive_probability`: chance de usuário ser positivo.
- `profile.active_days_min` e `profile.active_days_max`: faixa de dias ativos.
- `profile.sessions_min` e `profile.sessions_max`: faixa de sessões por dia.
- `profile.hour_buckets`: horários prováveis para os eventos.
- `profile.primary_features`: features principais do usuário.
- `profile.secondary_features`: features secundárias.

### Heurísticas de comportamento

- usuários são distribuídos de forma determinística por catálogo;
- cada perfil define um comportamento diferente;
- a probabilidade de conversão varia por perfil;
- dias ativos e sessões são sorteados dentro de faixas controladas;
- os horários dos eventos são escolhidos de buckets pré-definidos;
- eventos de conversão aparecem mais tarde na jornada;
- o último dia/sessão de um usuário positivo tende a concentrar o evento de conversão.

### Sequência de eventos gerados

Para cada sessão:

1. cria um evento de exposição;
2. cria um evento de exposição da feature principal;
3. opcionalmente cria um evento de comparação em outra feature;
4. se o usuário for positivo, cria um evento positivo;
5. se houver conversão, cria um evento de conversão.

### Campos gravados em cada evento

- `user_id`
- `feature_key`
- `event_type`
- `timestamp`
- `source`
- `properties`

`properties` carrega metadados como:

- `catalog_name`
- `seed_source`
- `seed_version`
- `journey`
- `stage`
- `segment`
- `device`
- `country`
- `channel`
- `session_id`
- `user_alias`
- `page`
- `surface`
- `funnel_stage`
- `flag_variant`
- `latency_ms`
- `step_index`
- `day_offset`

Quando existe pedido de valor financeiro:

- `order_value`
- `currency`

## 4) Heurísticas e cálculos

### 4.1 `latency_ms`

O seed usa uma faixa de latência por tipo de evento.

Exemplos:

- exposições têm latência menor;
- cliques e interações têm latência intermediária;
- conversões têm latência maior.

Isso faz os eventos parecerem mais realistas e ajuda a testar a validação de ingestão.

### 4.2 `flag_variant`

O seed alterna `flag_variant` entre `control` e `treatment` com base em dia e sessão.
Esse valor não substitui `ab_variant`; ele é apenas um metadado sintético.

### 4.3 Idempotência

O script evita duplicação por identidade lógica do evento:

- `user_id`
- `feature_key`
- `event_type`
- `timestamp` normalizado em UTC sem microsegundos

Se o evento já existir, ele é ignorado.

## 5) Relação com o resto do sistema

O `dataset/` alimenta:

- o seed local;
- a tabela `activities`;
- a tabela `features`;
- a tabela `events`;
- o treino batch;
- a avaliação em `/evaluate`;
- a simulação de experimentos.

## 6) Quando usar este doc

Use este arquivo quando precisar entender:

- por que o seed gera certos padrões;
- quais campos os JSON precisam ter;
- como os eventos viram dados persistidos;
- quais heurísticas fazem o seed parecer realista.

## 7) Onde ficam os cálculos

Os cálculos de machine learning, avaliação e experimento já estão detalhados em outros docs:

- [`ml-train-and-feature-builder.md`](ml-train-and-feature-builder.md)
- [`ml-evaluation-decision-flow.md`](ml-evaluation-decision-flow.md)
- [`experiment-decision-flow.md`](experiment-decision-flow.md)
