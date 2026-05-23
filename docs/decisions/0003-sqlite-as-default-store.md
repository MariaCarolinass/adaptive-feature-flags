# 0003 - SQLite as Default Persistence for MVP

- Status: Accepted
- Data: 2026-05-23

## Contexto

MVP prioriza rapidez de setup, reprodutibilidade local e baixo custo operacional para validação de arquitetura e fluxo de decisão.

## Decisão

Usar SQLite como armazenamento padrão no MVP, com repositórios concretos em `app/infrastructure/repositories`.

## Consequencias

- Positivas: setup simples, baixa fricção para contribuidores, testes locais rápidos.
- Negativas: limitações de concorrência e escalabilidade.
- Riscos: acoplamento excessivo a detalhes SQLite se interfaces de repositório não forem respeitadas.
