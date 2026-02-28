# Projeto 4 - Frontend + Backend (LojaControl)

Aplicacao full stack para simulacao de loja com painel administrativo e area do cliente.

## Funcionalidades

- Cadastro e login de usuarios
- Login administrativo
- Catalogo de produtos
- Compra de produtos com controle de saldo
- Recarga de saldo para usuarios
- Listagem de pedidos (usuario e admin)
- Configuracao visual basica do site

## Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python + FastAPI
- Persistencia: arquivo JSON (`loja_db.json`)

## Estrutura do projeto

- `index.html`: interface principal
- `style.css`: estilos da aplicacao
- `script.js`: logica do frontend
- `testebackend.py`: API FastAPI e servicos
- `loja_db.json`: base de dados local
- `requirements.txt`: dependencias Python

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

3. Subir o servidor:

```powershell
python -m uvicorn testebackend:app --host 127.0.0.1 --port 8000
```

4. Acessar no navegador:

- App: `http://127.0.0.1:8000`
- Docs da API: `http://127.0.0.1:8000/docs`

## Credenciais administrativas padrao

- Email: `admin@lojacontrol.local`
- Senha: `admin123`

Voce pode alterar usando variaveis de ambiente:

- `LOJA_ADMIN_EMAIL`
- `LOJA_ADMIN_PASSWORD`

## Objetivo

Projeto de estudo para praticar integracao entre frontend e backend, autenticacao, CRUD e fluxo de compra.
