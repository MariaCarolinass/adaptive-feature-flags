# Fluxo de decisao: Rollout e ML

Este documento descreve como a API decide se uma feature sera habilitada para um usuario, combinando rollout deterministico e score de modelo.

## Objetivo

O sistema suporta dois mecanismos de decisao:

- Rollout deterministico por percentual (`rollout_percentage`)
- Decisao orientada por score de ML quando a feature permite (`ml_enabled`)

A avaliacao acontece no endpoint `POST /evaluate`.

## Componentes envolvidos

- `app/api/v1/routes/evaluate.py`: entrada HTTP da avaliacao.
- `app/domain/services/evaluation_service.py`: regra principal de decisao.
- `app/domain/services/training_service.py`: orquestracao de treino.
- `app/infrastructure/ml/trainer.py`: treinamento e persistencia do artefato.
- `app/infrastructure/ml/feature_builder.py`: engenharia de features para treino e inferencia.

## Pre-condicoes para decisao via ML

Para a decisao usar ML no `/evaluate`, todos os itens abaixo precisam ser verdadeiros:

1. A feature existe.
2. A feature esta habilitada (`enabled=true`).
3. A feature permite ML (`ml_enabled=true`).
4. O status do modelo esta `ready`.
5. Existe `artifact_path` no metadado do modelo.
6. O score de ML foi calculado com sucesso.

Se qualquer condicao falhar, a API usa rollout deterministico.

## Fluxo de decisao no /evaluate

Sequencia simplificada:

1. Buscar a feature por `feature_key`.
2. Se nao existir: retorna `enabled=false` e `decision_source="feature_not_found"`.
3. Se existir mas estiver desabilitada: retorna `enabled=false` e `decision_source="feature_disabled"`.
4. Se `ml_enabled=true` e o modelo estiver pronto:
   - carrega eventos do usuario;
   - gera features com `FeatureBuilder`;
   - carrega colunas esperadas do artefato;
   - calcula score com `ModelPredictor`.
5. Se score valido: retorna `decision_source="ml"` e habilita quando `score >= 0.1`.
6. Se score indisponivel/falhar: aplica rollout deterministico e retorna `decision_source="rollout"`.

### Diagrama de sequencia (texto)

```text
Cliente -> API /evaluate: feature_key + user_id
API /evaluate -> EvaluationService: evaluate(feature_key, user)
EvaluationService -> FeatureRepository: get_by_key(feature_key)

alt feature nao encontrada
  EvaluationService --> Cliente: feature_not_found (enabled=false)
else feature desabilitada
  EvaluationService --> Cliente: feature_disabled (enabled=false)
else feature ativa
  EvaluationService -> ModelRepository: get_status()
  alt ml_enabled=true e modelo ready com artifact_path
    EvaluationService -> EventRepository: list(user_id)
    EvaluationService -> FeatureBuilder: build_from_dataframe(user_events)
    EvaluationService -> ModelSerializer: load_feature_columns(artifact_path)
    EvaluationService -> ModelPredictor: predict_score(payload)
    alt score valido
      EvaluationService --> Cliente: decision_source=ml (score >= 0.1)
    else erro/score indisponivel
      EvaluationService -> Hash rollout: sha256(user_id:feature_key) % 100
      EvaluationService --> Cliente: decision_source=rollout
    end
  else ml indisponivel
    EvaluationService -> Hash rollout: sha256(user_id:feature_key) % 100
    EvaluationService --> Cliente: decision_source=rollout
  end
end
```

### Diagrama de sequencia (Mermaid)

```mermaid
sequenceDiagram
    participant C as Cliente
    participant API as API /evaluate
    participant ES as EvaluationService
    participant FR as FeatureRepository
    participant MR as ModelRepository
    participant ER as EventRepository
    participant FB as FeatureBuilder
    participant MS as ModelSerializer
    participant MP as ModelPredictor
    participant RO as Rollout Hash

    C->>API: POST /evaluate (feature_key, user_id)
    API->>ES: evaluate(feature_key, user)
    ES->>FR: get_by_key(feature_key)

    alt feature nao encontrada
        ES-->>C: feature_not_found (enabled=false)
    else feature desabilitada
        ES-->>C: feature_disabled (enabled=false)
    else feature ativa
        ES->>MR: get_status()
        alt ml_enabled=true e modelo ready com artifact_path
            ES->>ER: list(user_id)
            ES->>FB: build_from_dataframe(user_events)
            ES->>MS: load_feature_columns(artifact_path)
            ES->>MP: predict_score(payload)
            alt score valido
                ES-->>C: decision_source=ml (enabled = score >= 0.1)
            else score indisponivel/erro
                ES->>RO: sha256(user_id:feature_key) % 100
                ES-->>C: decision_source=rollout
            end
        else ML indisponivel
            ES->>RO: sha256(user_id:feature_key) % 100
            ES-->>C: decision_source=rollout
        end
    end
```

## Como funciona o rollout deterministico

O rollout usa hash estavel por par `(user_id, feature_key)`:

- calcula `sha256(f"{user_id}:{feature_key}")`
- converte parte do hash em bucket de `0..99`
- habilita quando `bucket < rollout_percentage`

Isso garante consistencia: o mesmo usuario recebe sempre a mesma decisao para a mesma feature, enquanto o percentual permanecer igual.

## Treino do modelo (sincrono e assincrono)

### Treino sincrono

- Endpoint: `POST /train`
- Fonte de dados: eventos persistidos
- Passos:
  - monta dataset por usuario via `FeatureBuilder`;
  - define alvo binario (`target`);
  - treina `RandomForestClassifier`;
  - calcula metricas (`accuracy`, `f1_score`);
  - salva artefato em `MODELS_DIR`;
  - atualiza `model_metadata` com status `ready`.

### Treino assincrono

- Iniciar: `POST /train/async`
- Consultar: `GET /train/jobs/{job_id}`
- Status global de modelo: `GET /model/status`
- Persistencia de job: tabela `training_jobs` (SQLite)
- Durabilidade: status de job sobrevive a restart do processo da API
- Retencao: jobs antigos terminais (`succeeded`/`failed`) sao removidos por politica de tempo/capacidade

## Importacao de dataset para simulacao

Para preparar ambiente de teste de ponta a ponta (eventos -> treino -> evaluate), use:

- Endpoint: `POST /simulate`
- Fonte de entrada: exatamente uma entre `csv_url` ou `csv_file` (multipart/form-data)
- Formato esperado: CSV estilo Retailrocket com colunas
  - `timestamp`
  - `visitorid`
  - `event`
  - `itemid`

Parametros principais:

- `feature_key_mode`:
  - `item` -> `feature_key=item_<itemid>`
  - `single` -> `feature_key=retailrocket_import`
- `sync_features` (default: `true`): auto-cria features ausentes
- `feature_rollout_percentage` (default: `10`)
- `feature_ml_enabled` (default: `true`)
- `limit`, `chunk_size`, `batch_size` para controle de volume/performance

### Diagrama de sequencia do treino (Mermaid)

```mermaid
sequenceDiagram
    participant C as Cliente
    participant API as API /train
    participant TAPI as API /train/async
    participant TS as TrainingService
    participant TJS as TrainingJobService
    participant ER as EventRepository
    participant TR as Trainer
    participant FB as FeatureBuilder
    participant RF as RandomForestClassifier
    participant MS as ModelSerializer
    participant MR as ModelRepository

    rect rgb(245, 245, 245)
    Note over C,MR: Fluxo sincrono
    C->>API: POST /train
    API->>TS: train()
    TS->>ER: list()
    TS->>TR: train_from_events(events)
    TR->>FB: build_from_dataframe(df)
    TR->>RF: fit(X_train, y_train)
    TR->>MS: save(model, metrics, feature_columns)
    TR-->>TS: artifact_path + metrics + version
    TS->>MR: save_status(status=ready, artifact_path, metrics)
    TS-->>C: metadados + process
    end

    rect rgb(245, 245, 245)
    Note over C,MR: Fluxo assincrono
    C->>TAPI: POST /train/async
    TAPI->>TJS: start()
    TJS-->>C: 202 Accepted + job_id
    C->>TAPI: GET /train/jobs/{job_id}
    TAPI->>TJS: get(job_id)
    TJS-->>C: pending/running/done/failed (+ result/erro)
    end
```

## Condicoes de fallback para rollout

A API faz fallback para rollout quando:

- nao ha eventos para o usuario;
- nao foi possivel montar dataset de inferencia;
- faltam colunas esperadas pelo artefato;
- ocorreu erro ao carregar artefato/modelo;
- ocorreu erro ao predizer score;
- modelo nao esta `ready` ou sem `artifact_path`.

Nesses casos, o endpoint continua respondendo com decisao valida usando rollout, evitando indisponibilidade da feature flag.

## Interpretacao do campo decision_source

Valores possiveis de `decision_source`:

- `feature_not_found`: chave de feature inexistente.
- `feature_disabled`: feature existe, mas esta desligada.
- `ml`: decisao feita com score de modelo.
- `rollout`: decisao feita por percentual deterministico.

## Exemplo de chamada

```bash
curl -X POST "http://localhost:8000/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"feature_key":"item_355908","user":{"user_id":"257597"}}'
```

Resposta (exemplo com ML):

```json
{
  "feature_key": "item_355908",
  "user_id": "257597",
  "enabled": true,
  "decision_source": "ml",
  "score": 0.42,
  "model_version": "v1"
}
```

Resposta (exemplo com fallback para rollout):

```json
{
  "feature_key": "item_355908",
  "user_id": "257597",
  "enabled": false,
  "decision_source": "rollout",
  "score": null,
  "model_version": null
}
```

## Operacao recomendada

- Treinar novamente apos mudancas relevantes de comportamento dos usuarios.
- Monitorar `decision_source` em producao para acompanhar proporcao `ml` vs `rollout`.
- Revisar periodicamente metricas e threshold de ativacao de ML.
- Usar `scripts/test_model.py` para comparar ML vs baseline de rollout offline.
- Monitorar o volume de `training_jobs` e ajustar retencao se necessario para seu ambiente.
