# Política de Segurança

## Versões suportadas

O foco de manutenção é a branch `main`.

## Reportar vulnerabilidades

Para reportar vulnerabilidade de forma responsável:

1. Não abra issue pública com detalhes sensíveis.
2. Envie um e-mail para: `felipecardoso1328@gmail.com`
3. Inclua:
   - Descrição do problema
   - Passos para reproduzir
   - Impacto potencial
   - Sugestão de mitigação (se tiver)

## Boas práticas já aplicadas

- Hash de senha com `passlib` + `bcrypt`
- JWT com expiração e refresh token rotativo
- Validação de payload com Pydantic
- Rate limiting
- Tratamento global de exceções
