# Documentação do Adaptive Feature Flags

Este diretório organiza a documentação em produto, arquitetura, API, decisões técnicas, implementação e operação.

## Comece por aqui

- Visão do projeto e escopo MVP: `product/mvp-product-vision.md`
- Visão técnica do sistema: `architecture/system-overview.md`
- Contratos da API: `api/README.md`
- Decisões técnicas (ADRs): `decisions/README.md`
- Implementações críticas de código: `implementation/critical-code-paths.md`
- Fluxo detalhado de ML e decisão online: `implementation/ml-decision-flow-in-depth.md`
- Guia de módulos de suporte (core/integrations/observability/sdk): `implementation/module-guide-core-and-support.md`
- Operação local e rotina de desenvolvimento: `operations/development-playbook.md`
- Guia da interface web: `operations/ui-dashboard.md`
- Roadmap incremental: `roadmap.md`

## Estrutura

### `product/`
- Contexto, objetivos, restrições, KPIs e impacto esperado.
- Estratégia de experimentação e posicionamento de teste A/B.

### `architecture/`
- Visão de componentes, fronteiras de camadas e fluxos (avaliação, treino e fallback).

### `api/`
- Documentação de endpoints, contratos de request/response e exemplos de uso.

### `decisions/`
- Registro histórico de decisões de arquitetura e tradeoffs.

### `implementation/`
- Mapa dos pontos do código que exigem maior cuidado para evolução.

### `operations/`
- Setup local, execução, testes e checklist operacional.
