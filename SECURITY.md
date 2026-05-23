# Política de Segurança

## Reportando vulnerabilidades

Se você identificar uma vulnerabilidade, não publique detalhes de exploração em issue pública.

Processo recomendado:

1. Abra uma issue com prefixo `[SECURITY]`.
2. Descreva apenas impacto e contexto em alto nível (sem PoC/exploit).
3. Solicite um canal privado para envio dos detalhes técnicos.

## O que incluir no reporte

- Componente afetado.
- Tipo de impacto (ex.: vazamento de dados, execução indevida, bypass de autorização).
- Pré-condições para exploração.
- Severidade estimada.

## Diretrizes de divulgação responsável

- Aguarde triagem antes de divulgar publicamente.
- Não compartilhe credenciais, payloads sensíveis ou dados de usuários.
- Coopere com validação e reteste após correção.

## Medidas de segurança já adotadas

- `TrustedHostMiddleware` com allowlist configurável (`TRUSTED_HOSTS`).
- CORS com allowlist configurável (`CORS_ALLOWED_ORIGINS`).
- Headers de segurança nas respostas.
- Respostas `500` sanitizadas (sem stack trace para cliente).

## Escopo desta política

Esta política cobre o código e a operação deste repositório. Dependências de terceiros devem ser reportadas também aos respectivos mantenedores quando aplicável.
