from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Order, OrderItem, Product, SiteConfig, User
from app.schemas.admin import ProdutoCreatePayload, ProdutoUpdatePayload, SiteConfigPayload
from app.services.shop_service import list_all_orders, product_payload


def _round_money(value: float) -> float:
    return round(float(value), 2)


def _site_config_payload(config: SiteConfig) -> dict:
    return {
        "site_name": config.site_name,
        "tagline": config.tagline,
        "hero_title": config.hero_title,
        "hero_subtitle": config.hero_subtitle,
        "accent_color": config.accent_color,
        "highlight_color": config.highlight_color,
    }


def get_summary(db: Session) -> dict:
    users_count = db.scalar(select(func.count(User.id))) or 0
    products_count = db.scalar(select(func.count(Product.id))) or 0
    orders_count = db.scalar(select(func.count(Order.id))) or 0
    revenue = db.scalar(select(func.coalesce(func.sum(Order.total), 0.0))) or 0.0
    total_balance = db.scalar(select(func.coalesce(func.sum(User.saldo), 0.0))) or 0.0

    return {
        "usuarios": int(users_count),
        "produtos": int(products_count),
        "pedidos": int(orders_count),
        "faturamento": _round_money(float(revenue)),
        "saldo_total": _round_money(float(total_balance)),
    }


def list_users(db: Session) -> list[dict]:
    users = db.scalars(select(User).order_by(User.id.asc())).all()
    return [
        {
            "id": item.id,
            "nome": item.nome,
            "email": item.email,
            "saldo": _round_money(item.saldo),
        }
        for item in users
    ]


def list_products(db: Session) -> list[dict]:
    products = db.scalars(select(Product).order_by(Product.id.asc())).all()
    return [product_payload(item) for item in products]


def create_product(db: Session, payload: ProdutoCreatePayload) -> dict:
    product = Product(
        nome=payload.nome.strip(),
        descricao=payload.descricao.strip(),
        preco=_round_money(payload.preco),
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product_payload(product)


def update_product(db: Session, product_id: int, payload: ProdutoUpdatePayload) -> dict:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto nao encontrado.")

    if payload.nome is not None:
        product.nome = payload.nome.strip()
    if payload.descricao is not None:
        product.descricao = payload.descricao.strip()
    if payload.preco is not None:
        product.preco = _round_money(payload.preco)

    db.add(product)
    db.commit()
    db.refresh(product)
    return product_payload(product)


def delete_product(db: Session, product_id: int) -> dict:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto nao encontrado.")

    sold_count = db.scalar(select(func.count(OrderItem.id)).where(OrderItem.product_id == product_id)) or 0
    if sold_count > 0:
        raise HTTPException(status_code=409, detail="Nao e possivel remover produto ja vendido.")

    payload = product_payload(product)
    db.delete(product)
    db.commit()
    return payload


def list_orders(db: Session) -> list[dict]:
    return list_all_orders(db)


def get_site_config(db: Session) -> dict:
    config = db.get(SiteConfig, 1)
    if not config:
        raise HTTPException(status_code=500, detail="Configuracao do site nao encontrada.")
    return _site_config_payload(config)


def update_site_config(db: Session, payload: SiteConfigPayload) -> dict:
    config = db.get(SiteConfig, 1)
    if not config:
        raise HTTPException(status_code=500, detail="Configuracao do site nao encontrada.")

    update_data = payload.model_dump()
    for key, value in update_data.items():
        setattr(config, key, value)

    db.add(config)
    db.commit()
    db.refresh(config)
    return _site_config_payload(config)

