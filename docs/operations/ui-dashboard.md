# Interface Web

## Visão Geral

A interface web é servida pela própria aplicação FastAPI e fica disponível na rota principal:

```text
http://127.0.0.1:8000/
```

A rota `/` é a entrada oficial do produto.

## Como acessar

Com a API rodando:

- `http://127.0.0.1:8000/`

## Organização da tela

1. **Resumo**
- Mostra regras cadastradas, atividades registradas, estado do modelo e última atualização.
- Exibe o retorno da última ação de forma simples.
- Mantém detalhes técnicos recolhidos em "Ver detalhes da última ação".

2. **Insights**
- Mostra indicadores principais de avaliação.
- Compara decisões inteligentes com liberação gradual.
- Exibe gráficos de liberação, origem da decisão e tendência de eventos.

3. **Regras**
- Cria e atualiza regras de liberação.
- Configura percentual liberado, estratégia inteligente, sensibilidade e status da regra.
- Mostra regras cadastradas em uma tabela filtrável.

4. **Avaliação**
- Avalia um lote de usuários para a regra selecionada.
- Mostra resultado, origem da decisão, score, limite e variação.

5. **Atividades**
- Registra atividades individuais ou em lote.
- Filtra atividades por usuário, regra e tipo.
- Mostra eventos recentes com paginação.

6. **Treinos**
- Treina o modelo.
- Consulta status atual.
- Lista histórico de treinos.

## Melhorias de UX aplicadas

- Menu lateral limpo com navegação por seções.
- Páginas separadas por tarefa para evitar excesso de informação em uma tela só.
- Retorno técnico recolhido por padrão.
- Botões com estado de loading para feedback imediato.
- Tabelas com estados vazios claros.
- Fallback quando Chart.js não carregar.

## Observação sobre banco SQL

A interface **não acessa o SQLite diretamente no navegador**. A leitura ocorre via API, preservando a arquitetura e evitando expor detalhes de armazenamento no frontend.
