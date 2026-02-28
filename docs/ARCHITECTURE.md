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
2. Backend valida senha com hash (`passlib+bcrypt`) ou hash legado PBKDF2.
3. API gera `access_token` (JWT curto) e `refresh_token` (JWT longo).
4. O refresh token e armazenado no banco com `jti`, expiracao e estado de revogacao.
5. Requisicoes protegidas usam `Authorization: Bearer <access_token>`.
6. Middleware adiciona contexto de autenticacao (`request.state.auth_payload`).
7. Dependencias (`deps.py`) reforcam autorizacao por role (`admin` ou `user`).

## Persistencia

- Banco principal: SQLite (`loja.db`).
- Bootstrap inicial cria tabelas e garante conta admin.
- Se habilitado, importa dados legados de `loja_db.json` na primeira execucao.
- Para producao, schema deve ser evoluido via Alembic.

## Middlewares

- `AuthContextMiddleware`: extrai claims do JWT.
- `RequestLoggingMiddleware`: log estruturado por request (metodo, path, status, latencia, request_id).
- `RateLimitMiddleware`: limita requisicoes por IP em janela de tempo.

## Tratamento de erros

- Handler global para `HTTPException`.
- Handler global para validacao (`RequestValidationError`).
- Handler global para excecoes inesperadas (500) com `request_id`.

## Frontend

- `apiClient.js` centraliza comunicacao HTTP.
- `script.js` implementa estado da UI e fluxo das telas.
- A app consome endpoints reais do backend FastAPI.
- Quando `access_token` expira, frontend usa `refresh_token` para renovar sessao.
