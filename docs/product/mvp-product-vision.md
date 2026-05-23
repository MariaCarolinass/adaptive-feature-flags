# Visão de Produto do MVP

## Contexto

Sistemas digitais modernos precisam liberar funcionalidades de forma gradual para reduzir risco operacional e impacto negativo para usuários. O Smart Feature Flags nasce como iniciativa de P&D para estudar decisões de rollout orientadas por eventos de uso, indo além de estratégias fixas baseadas apenas em percentual.

## O que é este MVP

Uma API experimental para validar:

- Decisão de rollout com fallback seguro.
- Arquitetura evolutiva orientada a serviços.
- Integração entre eventos operacionais e mecanismos de decisão.

## Estratégia Event-Driven e Experimentação

O projeto adota uma estratégia orientada a eventos: sinais de uso (`view`, `addtocart`, `transaction`, etc.) alimentam o processo de decisão de rollout e o ciclo de aprendizado do modelo.

Nesta fase, a experimentação é tratada como capacidade progressiva:

- Base atual: rollout determinístico + avaliação por machine learning + fallback seguro.
- Objetivo de evolução: ampliar suporte a práticas de experimentação, incluindo cenários de teste A/B com maior governança.

Referência complementar: `experimentation-and-ab-testing.md`.

## O que o projeto é

- API experimental para apoiar decisões de rollout.
- Iniciativa de Pesquisa e Desenvolvimento.
- Prova de conceito para conectar sinais de uso a decisões operacionais.
- Base evolutiva para versões futuras.

## O que o projeto não é

- Produto final pronto para produção enterprise.
- Plataforma completa de analytics e observabilidade.
- Solução que elimina revisão humana de produto/engenharia.
- Sistema de decisão automática perfeita.

## Escopo funcional do MVP

### O que faz

- Cadastro e gestão de features.
- Definição de estratégia simples de rollout percentual.
- Ingestão de eventos de uso.
- Treino de modelo para apoio de decisão.
- Avaliação de liberação por usuário com fallback para rollout.

### O que não faz

- Dashboard visual nativo.
- Coleta automática universal de dados.
- Alteração automática irrestrita de rollout sem supervisão.
- Cobertura completa de experimentação de produto.

## Objetivos

- Estruturar API para decisões de rollout.
- Manter base simples, extensível e testável.
- Isolar componentes de decisão e análise.
- Viabilizar integrações futuras com plataformas externas.

## KPIs planejados

- Tempo médio de resposta da API.
- Disponibilidade da aplicação.
- Quantidade de eventos processados.
- Taxa de erro operacional.
- Cobertura de funcionalidades avaliadas.
- Estabilidade das funcionalidades liberadas.
- Qualidade percebida da recomendação de rollout.

## Restrições

- Escopo reduzido para validação rápida.
- Arquitetura inicial prioriza simplicidade e evolução gradual.
- Sem dashboard na fase inicial.
- Sem automação completa de decisão nesta etapa.
- Privacidade e anonimização devem ser consideradas em qualquer ampliação.

## Impacto esperado

- Redução de dependência de rollout puramente aleatório.
- Maior entendimento sobre decisão orientada por eventos.
- Base arquitetural para evolução incremental.
- Apoio a estudos de engenharia de software e produtos digitais.
