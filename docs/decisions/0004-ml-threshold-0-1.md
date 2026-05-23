# 0004 - Threshold de machine learning igual a 0.1 para habilitação

- Status: Accepted
- Data: 2026-05-23

## Contexto

O serviço de avaliação precisa transformar score contínuo de machine learning em decisão binária (`enabled=true/false`) com latência baixa e comportamento determinístico.

## Decisão

Usar `score >= 0.1` como regra de habilitação em decisões com `decision_source="ml"` no `EvaluationService`.

## Consequências

- Positivas: regra simples, previsível e fácil de monitorar.
- Negativas: limiar fixo pode não ser ótimo para todos os cenários.
- Riscos: drift de dados reduzir qualidade da decisão sem recalibração periódica.

## Alternativas consideradas

1. Limiar 0.5 fixo.
2. Limiar dinâmico por feature com calibração offline.
