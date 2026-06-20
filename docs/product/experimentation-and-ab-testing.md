# Experimentação e Teste A/B

## Papel no projeto

O Adaptive Feature Flags nasce com foco em decisões de rollout orientadas por eventos (Event-Driven). A experimentação é parte central da evolução do produto, mas com escopo intencionalmente incremental no MVP.

## Relação entre Event-Driven e A/B testing

- **Event-Driven**: coleta e usa sinais comportamentais reais para apoiar decisões.
- **A/B testing**: compara variantes para medir impacto causal em métricas de negócio.

```mermaid
flowchart LR
    A[Eventos de uso] --> B[Base Event-Driven]
    B --> C[Decisão operacional de rollout]
    B --> D[Análise de experimentação]
    D --> E[Hipótese A/B]
    E --> F[Decisão de evolução do rollout]
```

No contexto deste projeto, eventos são a base para ambos:

- Tomada de decisão operacional (habilitar ou não feature por usuário).
- Geração de evidências para experimentação e recomendação de rollout.

## Por que comparar A/B

A comparação A/B é útil porque transforma opinião em evidência prática.

- Mostra se uma variante realmente melhora a métrica escolhida.
- Reduz o risco de liberar uma mudança pior para toda a base.
- Ajuda a decidir com dados antes de escalar.
- Permite entender se a nova experiência funciona melhor do que a atual.

No produto, isso faz sentido porque:

- a decisão é por usuário e por regra;
- a variante é estável;
- a atividade de sucesso é definida;
- a decisão final só sai quando há volume suficiente.

## O que o MVP já oferece para experimentação

- Rollout determinístico por percentual.
- Coleta e ingestão canônica de eventos.
- Avaliação por machine learning com fallback seguro.
- Recomendação estratégica de rollout por feature.

## O que ainda não é um framework A/B completo

- Gestão nativa de variantes (A/B/n) com alocação por experimento.
- Cálculo estatístico de significância e intervalos de confiança.
- Regras de parada automática e guardrails formais.
- Dashboard de experimentos, auditoria e governança avançada.

## Direção de evolução

1. Introduzir modelo explícito de experimento (experimento, variante, hipótese, métricas-alvo).
2. Padronizar telemetria para análise causal.
3. Adicionar avaliação estatística e critérios de decisão.
4. Integrar recomendação de rollout com estado do experimento.

```mermaid
flowchart TD
    A[MVP atual<br/>rollout + machine learning + fallback] --> B[Fase 1<br/>modelo explícito de experimento]
    B --> C[Fase 2<br/>telemetria e análise causal]
    C --> D[Fase 3<br/>significância, guardrails e governança]
```

## Mensagem de posicionamento

O projeto não concorre, nesta fase, com plataformas completas de experimentação. Ele estabelece a base técnica para decisões de rollout orientadas por eventos e prepara o caminho para capacidades mais robustas de teste A/B.
