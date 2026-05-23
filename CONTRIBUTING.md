# Contribuindo para o Adaptive Feature Flags

Obrigado por contribuir.

## Requisitos

- Python 3.12+

## Setup local

```bash
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env
pip install -r requirements.txt
```

Rodar API local:

```bash
uvicorn app.main:app --reload
```

## Fluxo recomendado

1. Crie uma branch com escopo pequeno e objetivo.
2. Implemente mudanças mantendo compatibilidade com a arquitetura em camadas.
3. Execute testes e validações locais.
4. Atualize documentação quando houver mudança de comportamento.
5. Abra PR com contexto técnico e impacto esperado.

## Validações obrigatórias antes do PR

```bash
source .venv/bin/activate
pytest
python3 -m compileall -q app tests
```

## Padrões do projeto

- Arquitetura: `domain -> infrastructure -> api`.
- CRUD: contrato de repositório -> service -> repositório concreto -> rota/schema.
- Erros: use exceções tipadas em `app/core/exceptions.py` e mapeie com `to_http_exception()`.
- Segurança: não exponha detalhes internos em erros `500`.

## Configurações e documentação

Sempre que adicionar, renomear ou remover configurações em `app/core/config.py`, sincronize:

- `app/core/config.py`
- `.env.example`
- `README.md`
- `docs/` (quando houver impacto funcional ou operacional)

## Pull Requests

Inclua no PR:

- Contexto do problema.
- Resumo da solução.
- Riscos e tradeoffs.
- Evidência de teste (comandos executados).

Checklist:

- [ ] testes passando (`pytest`)
- [ ] `compileall` passando
- [ ] sem rotas sem suporte em service/repositório
- [ ] documentação atualizada quando aplicável

## Issues

Ao abrir issue, inclua:

- Passo a passo para reproduzir.
- Comportamento esperado vs atual.
- Versão do Python e comando usado para executar a API.

## Conduta e segurança

- Conduta: `CODE_OF_CONDUCT.md`
- Segurança: `SECURITY.md`
