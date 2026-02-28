# Arquitetura do Projeto

## Visao geral

O backend segue um modelo de camadas para manter responsabilidades separadas:

- `app/api/routers`: recebe requests HTTP e chama servicos.
- `app/services`: concentra regras de negocio.
- `app/schemas`: validacao dos payloads com Pydantic.
- `app/db`: modelos SQLAlchemy, sessao e bootstrap de banco.
- `app/core`: configuracoes e seguranca (JWT/hash).

## Fluxo de autenticacao

1. Usuario/admin faz login.
2. Backend valida senha com hash (`bcrypt`) ou hash legado PBKDF2.
3. API gera JWT com `sub` (id da conta) e `role`.
4. Requisicoes protegidas usam `Authorization: Bearer <token>`.
5. Dependencias (`deps.py`) validam token e papel da conta (`admin` ou `user`).

## Persistencia

- Banco principal: SQLite (`loja.db`).
- Bootstrap inicial cria tabelas e garante conta admin.
- Se habilitado, importa dados legados de `loja_db.json` na primeira execucao.

## Frontend

- `apiClient.js` centraliza comunicacao HTTP.
- `script.js` implementa estado da UI e fluxo das telas.
- A app consome endpoints reais do backend FastAPI.
