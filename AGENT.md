# Adaptive Feature Flags — Engineering Rules

Este arquivo define as regras obrigatórias para mudanças no projeto.

## 1) Arquitetura (obrigatório)

- Padrão: `domain -> infrastructure -> api` (Layered + DDD lite).
- `domain` não pode importar FastAPI, SQLAlchemy ou detalhes de framework.
- Regras de negócio ficam em `app/domain/services`.
- Acesso a dados deve passar por contratos em `app/domain/repositories`.

## 2) Organização de código

- `app/domain/`: entidades, contratos e serviços.
- `app/infrastructure/`: banco, repositórios concretos, machine learning, observabilidade e integrações.
- `app/api/` + `app/schemas/`: rotas HTTP e contratos de entrada/saída.
- `app/core/`: configuração, logging e exceções.

## 3) Fluxo padrão para CRUD

1. Definir/ajustar contrato em `app/domain/repositories/*`.
2. Aplicar validações e regras em `app/domain/services/*`.
3. Implementar persistência em `app/infrastructure/repositories/*`.
4. Expor rota em `app/api/v1/routes/*` com schema em `app/schemas/*`.

Não criar rota sem suporte real em service/repositório.

## 4) Regras de API

- Usar exceções tipadas de `app/core/exceptions.py`.
- Mapear erro de domínio para HTTP via `to_http_exception()`.
- Não vazar detalhes internos em respostas `500`.
- Códigos esperados:
  - `404`: recurso não encontrado
  - `409`: conflito de estado
  - `204`: remoção sem corpo
  - `500`: erro inesperado sanitizado

## 5) Banco e inicialização

- Persistência padrão: SQLAlchemy + SQLite.
- URL padrão: `sqlite:///./db.sqlite3` (via `DATABASE_URL`).
- `init_db()` deve executar no startup (`lifespan`) em `app/main.py`.
- IDs de entidade: inteiro autoincremental.
- Campos flexíveis (dicionário): `JSON`.

## 6) Segurança e runtime

- Respeitar `Settings` em `.env`/`app/core/config.py`.
- Variáveis críticas:
  - `ENVIRONMENT`, `LOG_LEVEL`, `ENABLE_DOCS`
  - `TRUSTED_HOSTS`, `CORS_ALLOWED_ORIGINS`
- Manter middlewares de segurança ativos.
- Logging centralizado em `app/core/logging.py`.

## 7) Testes obrigatórios ao alterar código

```bash
source .venv/bin/activate
pytest
python3 -m compileall -q app tests
```

Cobrir ao menos a camada impactada (`tests/services`, `tests/infrastructure/repositories`, `tests/api`).

## 8) Regras de documentação

Sempre que houver mudança funcional:

- Atualizar `README.md` se afetar uso/setup.
- Atualizar `.env.example` se configuração mudar.
- Atualizar `docs/` quando endpoint, fluxo de negócio ou decisão técnica mudar.
- Registrar decisão relevante em `docs/decisions/` (ADR).

## 9) Checklist de PR

- Camadas consistentes e desacopladas.
- Rota, service e repositório alinhados.
- Sem endpoint “fantasma”.
- Testes e `compileall` passando.
- Documentação sincronizada com a mudança.
