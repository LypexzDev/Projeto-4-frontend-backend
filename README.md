# LojaControl

[![CI](https://github.com/LypexzDev/Projeto-4-frontend-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/LypexzDev/Projeto-4-frontend-backend/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Aplicacao full stack com painel administrativo e area do cliente para fluxo completo de loja: autenticacao, catalogo, pedidos e gestao.

## Destaques

- Arquitetura backend modular (`routers`, `services`, `schemas`, `db`, `core`)
- Persistencia com SQLite + SQLAlchemy
- Autenticacao com JWT + hash seguro com `bcrypt`
- Frontend consumindo API real com `fetch` via cliente dedicado
- Testes automatizados com `pytest` + `TestClient`
- CI no GitHub Actions

## Stack

- Frontend: HTML5, CSS3, JavaScript
- Backend: FastAPI
- Database: SQLite
- ORM: SQLAlchemy 2.x
- Auth: JWT (`python-jose`) + `bcrypt`
- Testes: `pytest`, `httpx`, `TestClient`

## Estrutura

```text
.
|-- app/
|   |-- api/
|   |   |-- deps.py
|   |   `-- routers/
|   |-- core/
|   |-- db/
|   |-- schemas/
|   `-- services/
|-- tests/
|-- apiClient.js
|-- script.js
|-- style.css
|-- index.html
|-- testebackend.py
`-- requirements.txt
```

Documentacao tecnica: [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)

## Como executar

1. Criar e ativar ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

3. Subir a API:

```powershell
python -m uvicorn testebackend:app --host 127.0.0.1 --port 8000 --reload
```

4. Acessar:

- App: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

## Testes

```powershell
pytest -q
```

## Configuracao de ambiente

Copie `.env.example` e ajuste valores conforme seu ambiente.

Variaveis disponiveis:

- `LOJACONTROL_DATABASE_URL` (ex.: `sqlite:///C:/caminho/loja.db`)
- `LOJACONTROL_JWT_SECRET`
- `LOJACONTROL_JWT_ALGORITHM`
- `LOJACONTROL_ACCESS_TOKEN_EXPIRE_MINUTES`
- `LOJACONTROL_SKIP_LEGACY_IMPORT`
- `LOJA_ADMIN_EMAIL`
- `LOJA_ADMIN_PASSWORD`

Credenciais admin padrao:

- Email: `admin@lojacontrol.local`
- Senha: `admin123`

## Endpoints principais

- `POST /auth/register-user`
- `POST /auth/login-user`
- `POST /auth/login-admin`
- `GET /auth/me`
- `GET /shop/produtos`
- `POST /shop/pedidos`
- `GET /admin/resumo`
- `POST /admin/produtos`

## Roadmap

- [ ] Deploy em nuvem (Render/Railway)
- [ ] Migrations com Alembic
- [ ] Cobertura de testes maior (edge cases e autorizacao)
- [ ] Pipeline com lint/format

## Licenca

Este projeto esta sob a licenca MIT. Veja [LICENSE](./LICENSE).
