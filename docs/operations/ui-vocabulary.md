# Vocabulário da Interface

Termos padrão usados na UI.

Nota: inclua apenas termos recorrentes e estáveis. Evite registrar rótulos pontuais para não transformar este arquivo em um dicionário de implementação.

## Termos padrão

- `Regras` = features.
- `Atividades` = eventos canônicos.
- `Testes` = experimentos.
- `Nome da regra` = rótulo exibido.
- `Identificador` = chave técnica.
- `Descrição curta` = resumo textual curto.
- `Resultado` = `Liberado` ou `Bloqueado`.
- `Pontuação` = score da decisão.
- `Variação` = diferença entre pontuação e corte.
- `Origem da decisão` = origem do resultado (`machine learning`, `rollout`, `feature_not_found`, `feature_disabled`).
- `Percentual de liberação` = cobertura gradual.
- `Pontuação mínima` = corte da decisão.
- `Acompanhar cobertura` = modo gradual.
- `Automática` = modo orientado por machine learning.
- `Situação do modelo` = estado atual do modelo.
- `Versão do modelo` = versão do artefato ativo.
- `Última atualização` = data da última mudança relevante.
- `Treino` = execução de treinamento.
- `Execução do treino` = registro histórico do treino.
- `Avaliações recentes` = tabela de decisões recentes.
- `Atividades recentes` = tabela de eventos recentes.
- `Regra avaliada` = feature usada na avaliação.
- `Atividade` = evento associado à avaliação.
- `Evento de sucesso` = atividade principal do teste.
- `Origem` = aplicação de origem do evento.

## Regra de uso

- A UI deve preferir esses termos em textos visíveis.
- Nomes técnicos continuam válidos em rotas, payloads, banco e código interno.
- Quando houver conflito entre termo técnico e termo de apresentação, a UI usa o termo de apresentação.
