from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import LEGACY_DATA_FILE, get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.models import Account, Order, OrderItem, Product, SiteConfig, User
from app.db.session import SessionLocal, engine

DEFAULT_SITE_CONFIG = {
    "site_name": "LojaControl",
    "tagline": "Painel comercial e compras online",
    "hero_title": "Gestao em tempo real",
    "hero_subtitle": "Um sistema unico para admin e clientes.",
    "accent_color": "#1ec8a5",
    "highlight_color": "#1ea4d8",
}


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_legacy_timestamp(value: Any) -> datetime:
    if not value:
        return datetime.now(timezone.utc)

    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return datetime.now(timezone.utc)


def _load_legacy_payload() -> dict[str, Any]:
    if not LEGACY_DATA_FILE.exists():
        return {}
    try:
        raw = json.loads(LEGACY_DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _database_is_empty(db: Session) -> bool:
    users_count = db.scalar(select(func.count(User.id))) or 0
    accounts_count = db.scalar(select(func.count(Account.id))) or 0
    products_count = db.scalar(select(func.count(Product.id))) or 0
    orders_count = db.scalar(select(func.count(Order.id))) or 0
    return users_count == 0 and accounts_count == 0 and products_count == 0 and orders_count == 0


def _ensure_site_config(db: Session, payload: dict[str, Any] | None = None) -> SiteConfig:
    merged = DEFAULT_SITE_CONFIG.copy()
    if isinstance(payload, dict):
        merged.update({key: value for key, value in payload.items() if key in merged and value})

    config = db.get(SiteConfig, 1)
    if not config:
        config = SiteConfig(id=1, **merged)
        db.add(config)
        db.flush()
        return config

    config.site_name = str(merged["site_name"])
    config.tagline = str(merged["tagline"])
    config.hero_title = str(merged["hero_title"])
    config.hero_subtitle = str(merged["hero_subtitle"])
    config.accent_color = str(merged["accent_color"])
    config.highlight_color = str(merged["highlight_color"])
    db.flush()
    return config


def _import_legacy_users(db: Session, legacy_users: list[dict[str, Any]]) -> None:
    for item in legacy_users:
        if not isinstance(item, dict):
            continue

        email = _normalize_email(str(item.get("email", "")))
        nome = str(item.get("nome", "")).strip()
        if not email or not nome:
            continue

        user_id = _to_int(item.get("id"))
        user = db.get(User, user_id) if user_id else db.scalar(select(User).where(User.email == email))

        if user:
            user.nome = nome
            user.email = email
            user.saldo = _to_float(item.get("saldo", 0))
            continue

        db.add(
            User(
                id=user_id if user_id else None,
                nome=nome,
                email=email,
                saldo=_to_float(item.get("saldo", 0)),
            )
        )

    db.flush()


def _import_legacy_products(db: Session, legacy_products: list[dict[str, Any]]) -> None:
    for item in legacy_products:
        if not isinstance(item, dict):
            continue

        nome = str(item.get("nome", "")).strip()
        if not nome:
            continue

        product_id = _to_int(item.get("id"))
        product = db.get(Product, product_id) if product_id else None
        if product:
            product.nome = nome
            product.descricao = str(item.get("descricao", "")).strip()
            product.preco = _to_float(item.get("preco", 0))
            continue

        db.add(
            Product(
                id=product_id if product_id else None,
                nome=nome,
                descricao=str(item.get("descricao", "")).strip(),
                preco=_to_float(item.get("preco", 0)),
            )
        )

    db.flush()


def _import_legacy_accounts(db: Session, legacy_accounts: list[dict[str, Any]]) -> None:
    for item in legacy_accounts:
        if not isinstance(item, dict):
            continue

        email = _normalize_email(str(item.get("email", "")))
        role = str(item.get("role", "user")).strip().lower()
        if role not in {"admin", "user"}:
            role = "user"
        if not email:
            continue

        account = db.scalar(select(Account).where(Account.email == email))
        if account:
            continue

        user_id = _to_int(item.get("usuario_id"))
        if user_id and not db.get(User, user_id):
            user_id = None

        legacy_hash = str(item.get("password_hash", "")).strip()
        if not legacy_hash:
            continue

        legacy_salt = str(item.get("salt", "")).strip() or None
        password_algo = "pbkdf2" if legacy_salt else "bcrypt"

        account_id = _to_int(item.get("id"))
        db.add(
            Account(
                id=account_id if account_id else None,
                nome=str(item.get("nome", "Usuario")).strip() or "Usuario",
                email=email,
                role=role,
                usuario_id=user_id,
                password_hash=legacy_hash,
                password_salt=legacy_salt,
                password_algo=password_algo,
            )
        )

    db.flush()


def _import_legacy_orders(db: Session, legacy_orders: list[dict[str, Any]]) -> None:
    price_by_product_id = {item.id: float(item.preco) for item in db.scalars(select(Product))}

    for item in legacy_orders:
        if not isinstance(item, dict):
            continue

        order_id = _to_int(item.get("id"))
        if order_id and db.get(Order, order_id):
            continue

        user_id = _to_int(item.get("usuario_id"))
        if not user_id or not db.get(User, user_id):
            continue

        product_ids_raw = item.get("produtos_ids", [])
        if not isinstance(product_ids_raw, list):
            continue

        valid_product_ids = []
        for raw_pid in product_ids_raw:
            pid = _to_int(raw_pid)
            if pid and pid in price_by_product_id:
                valid_product_ids.append(pid)

        if not valid_product_ids:
            continue

        calculated_total = round(sum(price_by_product_id[pid] for pid in valid_product_ids), 2)
        provided_total = _to_float(item.get("total"), calculated_total)

        order = Order(
            id=order_id if order_id else None,
            usuario_id=user_id,
            total=provided_total if provided_total > 0 else calculated_total,
            created_at=_parse_legacy_timestamp(item.get("created_at")),
        )
        db.add(order)
        db.flush()

        for product_id in valid_product_ids:
            db.add(OrderItem(order_id=order.id, product_id=product_id))

    db.flush()


def _import_legacy_data(db: Session, payload: dict[str, Any]) -> None:
    legacy_users = payload.get("usuarios")
    if isinstance(legacy_users, list):
        _import_legacy_users(db, legacy_users)

    legacy_products = payload.get("produtos")
    if isinstance(legacy_products, list):
        _import_legacy_products(db, legacy_products)

    legacy_accounts = payload.get("contas")
    if isinstance(legacy_accounts, list):
        _import_legacy_accounts(db, legacy_accounts)

    legacy_orders = payload.get("pedidos")
    if isinstance(legacy_orders, list):
        _import_legacy_orders(db, legacy_orders)

    site_config_payload = payload.get("site_config")
    _ensure_site_config(db, site_config_payload if isinstance(site_config_payload, dict) else None)


def _ensure_admin_account(db: Session) -> None:
    settings = get_settings()
    admin = db.scalar(select(Account).where(Account.role == "admin"))

    if admin:
        admin.email = settings.admin_email
        admin.nome = admin.nome or "Administrador"
        if not admin.password_hash:
            admin.password_hash = hash_password(settings.admin_password)
            admin.password_algo = "bcrypt"
            admin.password_salt = None
        db.flush()
        return

    same_email_account = db.scalar(select(Account).where(Account.email == settings.admin_email))
    if same_email_account:
        same_email_account.role = "admin"
        same_email_account.usuario_id = None
        if not same_email_account.password_hash:
            same_email_account.password_hash = hash_password(settings.admin_password)
            same_email_account.password_algo = "bcrypt"
            same_email_account.password_salt = None
        db.flush()
        return

    db.add(
        Account(
            nome="Administrador",
            email=settings.admin_email,
            role="admin",
            usuario_id=None,
            password_hash=hash_password(settings.admin_password),
            password_salt=None,
            password_algo="bcrypt",
        )
    )
    db.flush()


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    settings = get_settings()

    with SessionLocal() as db:
        try:
            if _database_is_empty(db) and not settings.skip_legacy_import:
                payload = _load_legacy_payload()
                if payload:
                    _import_legacy_data(db, payload)

            _ensure_site_config(db)
            _ensure_admin_account(db)
            db.commit()
        except Exception:
            db.rollback()
            raise
