# Fluxo de Decisão de Avaliação (Rollout + Machine Learning)

Este documento descreve como a API decide se uma feature será habilitada para um usuário no endpoint `POST /evaluate`.

## Objetivo

Combinar dois mecanismos de decisão:

- Rollout determinístico por percentual (`rollout_percentage`).
- Decisão orientada por score de machine learning quando permitido (`ml_enabled=true`).

## Componentes envolvidos

- `app/api/v1/routes/evaluate.py`: entrada HTTP.
- `app/domain/services/evaluation_service.py`: regra principal de decisão.
- `app/domain/services/event_service.py`: leitura dos eventos persistidos.
- `app/domain/services/experiment_service.py`: contexto de experimento quando ativo.
- `app/domain/services/training_service.py`: orquestração de treino e status de modelo.
- `app/infrastructure/ml/feature_builder.py`: engenharia de features para inferência.
- `app/infrastructure/ml/predictor.py`: cálculo de score.
- `app/infrastructure/ml/serializer.py`: leitura de colunas esperadas no artefato.

## Pré-condições para usar machine learning no `/evaluate`

1. A feature existe.
2. A feature está habilitada (`enabled=true`).
3. A feature permite machine learning (`ml_enabled=true`).
4. O status do modelo está `ready`.
5. Existe `artifact_path` no metadado do modelo.
6. O score de machine learning é calculado com sucesso.

Se qualquer condição falhar, a API usa rollout determinístico.

## Sequência de decisão no `/evaluate`

1. Buscar feature por `feature_key`.
2. Se não existir: retorna `enabled=false` e `decision_source="feature_not_found"`.
3. Se existir mas estiver desabilitada: retorna `enabled=false` e `decision_source="feature_disabled"`.
4. Se `ml_enabled=true` e modelo `ready`, tenta inferência.
5. Se score válido, resolve o threshold da feature e retorna `decision_source="ml"` quando `score >= threshold`.
6. Se score indisponível/falhar ou o modelo não estiver aplicável: aplica rollout determinístico com `decision_source="rollout"`.

```mermaid
flowchart TD
    A[Request: feature_key + user_id] --> B[Buscar feature]
    B --> C{Feature existe?}
    C -- Não --> D[feature_not_found / enabled=false]
    C -- Sim --> E{Feature habilitada?}
    E -- Não --> F[feature_disabled / enabled=false]
    E -- Sim --> G{ml_enabled e modelo ready?}
    G -- Não --> H[Calcular bucket rollout]
    G -- Sim --> I[Tentar score de machine learning]
    I --> J{Score válido?}
    J -- Sim --> K[Resolver threshold da feature]
    K --> L[enabled = score >= threshold / source=ml]
    J -- Não --> H
    H --> M[enabled = bucket < rollout_percentage / source=rollout]
```

## Como a atividade é resolvida

- A decisão busca o evento mais recente para o mesmo `user_id` e `feature_key`.
- O campo `activity` na resposta recebe o `event_type` desse evento.
- Se não houver evento compatível, `activity` fica `null`.

## Como funciona o rollout determinístico

- Calcula `sha256(f"{user_id}:{feature_key}")`.
- Converte para bucket `0..99`.
- Habilita quando `bucket < rollout_percentage`.

Isso garante consistência: mesmo par `(user_id, feature_key)` mantém a mesma decisão enquanto o percentual não mudar.

## Treino do modelo

### Síncrono

- Endpoint: `POST /train`.
- Fonte: eventos persistidos.
- Saída: artefato em `MODELS_DIR` + metadados com status `ready`.

## Como o threshold é escolhido

O threshold usado em machine learning depende de `ml_threshold_mode`:

- `fixed`: usa `ml_threshold_value`.
- `match_rollout`: aproxima o corte para manter a cobertura do rollout.
- `maximize_f1`: usa o melhor threshold encontrado no treino.

## Condições típicas de fallback para rollout

- Sem eventos do usuário.
- Dataset de inferência vazio.
- Colunas esperadas ausentes no payload.
- Erro ao carregar artefato/modelo.
- Erro na predição do score.
- Modelo sem status `ready` ou sem `artifact_path`.

## Interpretação de `decision_source`

- `feature_not_found`: feature inexistente.
- `feature_disabled`: feature desligada.
- `ml`: decisão por score de modelo.
- `rollout`: decisão por percentual determinístico.
