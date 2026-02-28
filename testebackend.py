from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "loja_db.json"
SESSION_TTL_SECONDS = 12 * 60 * 60

DEFAULT_SITE_CONFIG = {
    "site_name": "LojaControl",
    "tagline": "Painel comercial e compras online",
    "hero_title": "Gestao em tempo real",
    "hero_subtitle": "Um sistema unico para admin e clientes.",
    "accent_color": "#1ec8a5",
    "highlight_color": "#1ea4d8",
}


def default_store() -> Dict[str, Any]:
    return {
        "usuarios": [],
        "produtos": [],
        "pedidos": [],
        "contas": [],
        "site_config": DEFAULT_SITE_CONFIG.copy(),
    }


def normalize_email(email: str) -> str:
    return email.strip().lower()


def load_store() -> Dict[str, Any]:
    if not DATA_FILE.exists():
        return default_store()

    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_store()

    if not isinstance(raw, dict):
        return default_store()

    site_config = DEFAULT_SITE_CONFIG.copy()
    if isinstance(raw.get("site_config"), dict):
        site_config.update(raw["site_config"])

    return {
        "usuarios": raw.get("usuarios", []),
        "produtos": raw.get("produtos", []),
        "pedidos": raw.get("pedidos", []),
        "contas": raw.get("contas", []),
        "site_config": site_config,
    }


store = load_store()
usuarios_db: List[Dict[str, Any]] = store["usuarios"]
produtos_db: List[Dict[str, Any]] = store["produtos"]
pedidos_db: List[Dict[str, Any]] = store["pedidos"]
contas_db: List[Dict[str, Any]] = store["contas"]
site_config: Dict[str, Any] = store["site_config"]


def persist_store() -> None:
    payload = {
        "usuarios": usuarios_db,
        "produtos": produtos_db,
        "pedidos": pedidos_db,
        "contas": contas_db,
        "site_config": site_config,
    }
    DATA_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def get_next_id(items: List[Dict[str, Any]]) -> int:
    return max((int(item.get("id", 0)) for item in items), default=0) + 1


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 140000).hex()
    return salt, digest


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    _, generated = hash_password(password, salt)
    return hmac.compare_digest(generated, password_hash)


def find_account_by_email(email: str) -> Optional[Dict[str, Any]]:
    normalized = normalize_email(email)
    return next((item for item in contas_db if normalize_email(item.get("email", "")) == normalized), None)


def find_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    return next((item for item in usuarios_db if int(item.get("id", 0)) == int(user_id)), None)


def build_order_details(pedido: Dict[str, Any]) -> Dict[str, Any]:
    catalog = {item["id"]: item for item in produtos_db}
    produtos = []
    for produto_id in pedido.get("produtos_ids", []):
        produto = catalog.get(produto_id)
        if produto:
            produtos.append({"id": produto["id"], "nome": produto["nome"], "preco": produto["preco"]})

    usuario = find_user_by_id(pedido["usuario_id"])
    return {
        "id": pedido["id"],
        "usuario_id": pedido["usuario_id"],
        "usuario_nome": usuario["nome"] if usuario else "Desconhecido",
        "produtos_ids": pedido["produtos_ids"],
        "produtos": produtos,
        "total": pedido["total"],
        "created_at": pedido.get("created_at", ""),
    }


def current_timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def create_pedido_for_user(usuario_id: int, produtos_ids: List[int]) -> Dict[str, Any]:
    usuario = find_user_by_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")

    catalog = {item["id"]: item for item in produtos_db}
    produtos_validos = []
    invalidos = []
    for produto_id in produtos_ids:
        produto = catalog.get(produto_id)
        if produto:
            produtos_validos.append(produto)
        else:
            invalidos.append(str(produto_id))

    if invalidos:
        raise HTTPException(status_code=404, detail=f"Produto(s) invalido(s): {', '.join(invalidos)}.")

    total = round(sum(float(item["preco"]) for item in produtos_validos), 2)
    if float(usuario["saldo"]) < total:
        faltam = round(total - float(usuario["saldo"]), 2)
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Faltam R$ {faltam:.2f}.")

    usuario["saldo"] = round(float(usuario["saldo"]) - total, 2)
    novo_pedido = {
        "id": get_next_id(pedidos_db),
        "usuario_id": usuario_id,
        "produtos_ids": produtos_ids,
        "total": total,
        "created_at": current_timestamp(),
    }
    pedidos_db.append(novo_pedido)
    persist_store()
    return novo_pedido


def ensure_admin_account() -> None:
    admin_email = normalize_email(os.getenv("LOJA_ADMIN_EMAIL", "admin@lojacontrol.local"))
    admin_password = os.getenv("LOJA_ADMIN_PASSWORD", "admin123")
    existing = next((item for item in contas_db if item.get("role") == "admin"), None)

    if existing:
        existing["email"] = admin_email
        existing["nome"] = existing.get("nome", "Administrador")
        if not existing.get("salt") or not existing.get("password_hash"):
            salt, password_hash = hash_password(admin_password)
            existing["salt"] = salt
            existing["password_hash"] = password_hash
        persist_store()
        return

    salt, password_hash = hash_password(admin_password)
    conta_admin = {
        "id": get_next_id(contas_db),
        "nome": "Administrador",
        "email": admin_email,
        "role": "admin",
        "usuario_id": None,
        "salt": salt,
        "password_hash": password_hash,
    }
    contas_db.append(conta_admin)
    persist_store()


ensure_admin_account()


sessions: Dict[str, Dict[str, Any]] = {}


def create_session(conta_id: int) -> str:
    token = secrets.token_urlsafe(32)
    sessions[token] = {"conta_id": conta_id, "expires_at": time.time() + SESSION_TTL_SECONDS}
    return token


def remove_session(token: str) -> None:
    sessions.pop(token, None)


def clean_expired_sessions() -> None:
    now = time.time()
    for token, session_data in list(sessions.items()):
        if session_data["expires_at"] < now:
            sessions.pop(token, None)


def account_public_payload(conta: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "id": conta["id"],
        "nome": conta["nome"],
        "email": conta["email"],
        "role": conta["role"],
    }
    if conta.get("role") == "user" and conta.get("usuario_id"):
        usuario = find_user_by_id(int(conta["usuario_id"]))
        if usuario:
            payload["usuario_id"] = usuario["id"]
            payload["saldo"] = usuario["saldo"]
    return payload


def extract_token(authorization: Optional[str] = Header(default=None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente.")
    prefix, _, token = authorization.partition(" ")
    if prefix.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Formato de token invalido.")
    return token.strip()


def get_current_account(token: str = Depends(extract_token)) -> Dict[str, Any]:
    clean_expired_sessions()
    session_data = sessions.get(token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Sessao invalida ou expirada.")

    conta = next((item for item in contas_db if item["id"] == session_data["conta_id"]), None)
    if not conta:
        remove_session(token)
        raise HTTPException(status_code=401, detail="Conta nao encontrada.")
    return conta


def get_admin_account(conta: Dict[str, Any] = Depends(get_current_account)) -> Dict[str, Any]:
    if conta.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    return conta


def get_user_account(conta: Dict[str, Any] = Depends(get_current_account)) -> Dict[str, Any]:
    if conta.get("role") != "user":
        raise HTTPException(status_code=403, detail="Acesso restrito a usuarios.")
    if not conta.get("usuario_id"):
        raise HTTPException(status_code=400, detail="Conta sem perfil vinculado.")
    return conta


app = FastAPI(title="LojaControl API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterUserPayload(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=100)
    saldo_inicial: float = Field(default=0, ge=0)


class LoginPayload(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=100)


class ProdutoCreatePayload(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    descricao: str = Field(default="", max_length=300)
    preco: float = Field(gt=0)


class ProdutoUpdatePayload(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=2, max_length=120)
    descricao: Optional[str] = Field(default=None, max_length=300)
    preco: Optional[float] = Field(default=None, gt=0)


class CheckoutPayload(BaseModel):
    produtos_ids: List[int] = Field(min_length=1)


class RecargaPayload(BaseModel):
    valor: float = Field(gt=0)


class SiteConfigPayload(BaseModel):
    site_name: str = Field(min_length=2, max_length=60)
    tagline: str = Field(min_length=2, max_length=120)
    hero_title: str = Field(min_length=2, max_length=80)
    hero_subtitle: str = Field(min_length=2, max_length=180)
    accent_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    highlight_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")


@app.get("/site-config")
def get_site_config():
    return site_config


@app.post("/auth/register-user")
def register_user(payload: RegisterUserPayload):
    email = normalize_email(payload.email)
    if find_account_by_email(email):
        raise HTTPException(status_code=409, detail="Ja existe uma conta com este e-mail.")

    usuario = next((item for item in usuarios_db if normalize_email(item.get("email", "")) == email), None)
    if usuario is None:
        usuario = {
            "id": get_next_id(usuarios_db),
            "nome": payload.nome.strip(),
            "email": email,
            "saldo": round(payload.saldo_inicial, 2),
        }
        usuarios_db.append(usuario)

    salt, password_hash = hash_password(payload.password)
    nova_conta = {
        "id": get_next_id(contas_db),
        "nome": payload.nome.strip(),
        "email": email,
        "role": "user",
        "usuario_id": usuario["id"],
        "salt": salt,
        "password_hash": password_hash,
    }
    contas_db.append(nova_conta)
    persist_store()

    return {"message": "Conta criada com sucesso.", "account": account_public_payload(nova_conta)}


def login_by_role(payload: LoginPayload, role: str) -> Dict[str, Any]:
    conta = find_account_by_email(payload.email)
    if not conta or conta.get("role") != role:
        raise HTTPException(status_code=401, detail="Credenciais invalidas.")
    if not verify_password(payload.password, conta["salt"], conta["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciais invalidas.")

    token = create_session(conta["id"])
    return {"token": token, "account": account_public_payload(conta)}


@app.post("/auth/login-user")
def login_user(payload: LoginPayload):
    return login_by_role(payload, "user")


@app.post("/auth/login-admin")
def login_admin(payload: LoginPayload):
    return login_by_role(payload, "admin")


@app.get("/auth/me")
def auth_me(conta: Dict[str, Any] = Depends(get_current_account)):
    return {"account": account_public_payload(conta)}


@app.post("/auth/logout")
def auth_logout(token: str = Depends(extract_token)):
    remove_session(token)
    return {"ok": True}


@app.get("/shop/produtos")
def shop_listar_produtos():
    return produtos_db


@app.get("/shop/me")
def shop_me(conta: Dict[str, Any] = Depends(get_user_account)):
    usuario = find_user_by_id(int(conta["usuario_id"]))
    if not usuario:
        raise HTTPException(status_code=404, detail="Perfil de usuario nao encontrado.")
    return {"id": usuario["id"], "nome": usuario["nome"], "email": usuario["email"], "saldo": usuario["saldo"]}


@app.post("/shop/recarga")
def shop_recarga(payload: RecargaPayload, conta: Dict[str, Any] = Depends(get_user_account)):
    usuario = find_user_by_id(int(conta["usuario_id"]))
    if not usuario:
        raise HTTPException(status_code=404, detail="Perfil de usuario nao encontrado.")
    usuario["saldo"] = round(float(usuario["saldo"]) + payload.valor, 2)
    persist_store()
    return {"saldo": usuario["saldo"]}


@app.post("/shop/pedidos")
def shop_checkout(payload: CheckoutPayload, conta: Dict[str, Any] = Depends(get_user_account)):
    usuario = find_user_by_id(int(conta["usuario_id"]))
    if not usuario:
        raise HTTPException(status_code=404, detail="Perfil de usuario nao encontrado.")
    pedido = create_pedido_for_user(usuario["id"], payload.produtos_ids)
    return build_order_details(pedido)


@app.get("/shop/pedidos")
def shop_listar_pedidos(conta: Dict[str, Any] = Depends(get_user_account)):
    usuario_id = int(conta["usuario_id"])
    pedidos = [build_order_details(item) for item in pedidos_db if int(item["usuario_id"]) == usuario_id]
    pedidos.sort(key=lambda item: item["id"], reverse=True)
    return pedidos


@app.get("/admin/resumo")
def admin_resumo(_: Dict[str, Any] = Depends(get_admin_account)):
    faturamento = round(sum(float(item.get("total", 0)) for item in pedidos_db), 2)
    saldo_total = round(sum(float(item.get("saldo", 0)) for item in usuarios_db), 2)
    return {
        "usuarios": len(usuarios_db),
        "produtos": len(produtos_db),
        "pedidos": len(pedidos_db),
        "faturamento": faturamento,
        "saldo_total": saldo_total,
    }


@app.get("/admin/usuarios")
def admin_listar_usuarios(_: Dict[str, Any] = Depends(get_admin_account)):
    return usuarios_db


@app.get("/admin/produtos")
def admin_listar_produtos(_: Dict[str, Any] = Depends(get_admin_account)):
    return produtos_db


@app.post("/admin/produtos")
def admin_criar_produto(payload: ProdutoCreatePayload, _: Dict[str, Any] = Depends(get_admin_account)):
    produto = {
        "id": get_next_id(produtos_db),
        "nome": payload.nome.strip(),
        "descricao": payload.descricao.strip(),
        "preco": round(payload.preco, 2),
    }
    produtos_db.append(produto)
    persist_store()
    return produto


@app.patch("/admin/produtos/{produto_id}")
def admin_atualizar_produto(
    produto_id: int,
    payload: ProdutoUpdatePayload,
    _: Dict[str, Any] = Depends(get_admin_account),
):
    produto = next((item for item in produtos_db if int(item["id"]) == produto_id), None)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto nao encontrado.")

    if payload.nome is not None:
        produto["nome"] = payload.nome.strip()
    if payload.descricao is not None:
        produto["descricao"] = payload.descricao.strip()
    if payload.preco is not None:
        produto["preco"] = round(payload.preco, 2)

    persist_store()
    return produto


@app.delete("/admin/produtos/{produto_id}")
def admin_excluir_produto(produto_id: int, _: Dict[str, Any] = Depends(get_admin_account)):
    if any(produto_id in item.get("produtos_ids", []) for item in pedidos_db):
        raise HTTPException(status_code=409, detail="Nao e possivel remover produto ja vendido.")

    index = next((i for i, item in enumerate(produtos_db) if int(item["id"]) == produto_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Produto nao encontrado.")

    removido = produtos_db.pop(index)
    persist_store()
    return removido


@app.get("/admin/pedidos")
def admin_listar_pedidos(_: Dict[str, Any] = Depends(get_admin_account)):
    pedidos = [build_order_details(item) for item in pedidos_db]
    pedidos.sort(key=lambda item: item["id"], reverse=True)
    return pedidos


@app.get("/admin/site-config")
def admin_get_site_config(_: Dict[str, Any] = Depends(get_admin_account)):
    return site_config


@app.patch("/admin/site-config")
def admin_update_site_config(payload: SiteConfigPayload, _: Dict[str, Any] = Depends(get_admin_account)):
    site_config.update(payload.model_dump())
    persist_store()
    return site_config


@app.get("/")
def frontend_index():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/script.js")
def frontend_script():
    return FileResponse(BASE_DIR / "script.js", media_type="application/javascript")


@app.get("/style.css")
def frontend_style():
    return FileResponse(BASE_DIR / "style.css", media_type="text/css")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return {"ok": True}
