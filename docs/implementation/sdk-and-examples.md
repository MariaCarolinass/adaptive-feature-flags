# SDK e exemplos

Este documento resume o papel do `sdk/` e dos scripts em `examples/`, que servem como referência de integração externa com a API.

## `sdk/`

### Papel

- Expor um cliente Python mínimo para consumir a API sem depender da UI.
- Servir como base para integrações externas, automação e testes manuais.

### Arquivos

- `sdk/adaptiveflags/client.py`: cliente HTTP simples com métodos para `evaluate`, `track`, `train` e `model_status`.
- `sdk/adaptiveflags/__init__.py`: exporta `AdaptiveFlagsClient`.
- `sdk/__init__.py`: torna o pacote importável a partir da raiz do projeto.

### Contrato

- `evaluate(feature_key, user_id, context=None)`: chama `POST /evaluate`.
- `track(user_id, feature_key, event_type, properties=None)`: chama `POST /events`.
- `train()`: chama `POST /train`.
- `model_status()`: chama `GET /model/status`.

### Observação

- O SDK não faz parte do runtime da API.
- Ele depende da API estar acessível no `base_url` configurado.

## `examples/`

### Papel

- Demonstrar uso real do SDK em cenários simples.
- Servir como smoke test manual do contrato público.

### Arquivos

- `examples/python_client_example.py`: fluxo linear de registrar evento, treinar modelo, consultar status e avaliar feature.
- `examples/external_app_example.py`: simula uma aplicação externa que avalia a feature antes de renderizar a experiência.

### Como executar

Com a API em pé:

```bash
python3 examples/python_client_example.py
python3 examples/external_app_example.py
```

### O que validar

- Se o SDK consegue se conectar na API.
- Se os nomes de feature e atividade batem com o catálogo do dataset.
- Se a avaliação responde com `enabled`, `decision_source`, `score` e `threshold` coerentes com o estado atual.

### Base de dados demo

- Os exemplos foram alinhados ao catálogo `checkout_focus` do `dataset/seed_demo_checkout_focus.json`.
- Isso reduz divergência entre documentação, UI e dados de seed.

## Compatibilidade

Mudanças em:

- contratos da API,
- nomes de feature,
- nomes de atividades,
- ou formatos de resposta

devem ser refletidas no SDK e nos exemplos para evitar documentação falsa.
