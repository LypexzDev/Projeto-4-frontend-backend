from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Account, Order, OrderItem, Product, User


def _round_money(value: float) -> float:
    return round(float(value), 2)


def _format_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _get_user_for_account(db: Session, account: Account) -> User:
    if account.role != "user":
        raise HTTPException(status_code=403, detail="Acesso restrito a usuarios.")
    if not account.usuario_id:
        raise HTTPException(status_code=400, detail="Conta sem perfil vinculado.")

    user = db.get(User, int(account.usuario_id))
    if not user:
        raise HTTPException(status_code=404, detail="Perfil de usuario nao encontrado.")
    return user


def product_payload(product: Product) -> dict:
    return {
        "id": product.id,
        "nome": product.nome,
        "descricao": product.descricao,
        "preco": _round_money(product.preco),
    }


def order_payload(order: Order) -> dict:
    products = []
    for item in order.items:
        if not item.product:
            continue
        products.append(
            {
                "id": item.product.id,
                "nome": item.product.nome,
                "preco": _round_money(item.product.preco),
            }
        )

    return {
        "id": order.id,
        "usuario_id": order.usuario_id,
        "usuario_nome": order.user.nome if order.user else "Desconhecido",
        "produtos_ids": [item.product_id for item in order.items],
        "produtos": products,
        "total": _round_money(order.total),
        "created_at": _format_datetime(order.created_at),
    }


def list_products(db: Session) -> list[dict]:
    products = db.scalars(select(Product).order_by(Product.id.asc())).all()
    return [product_payload(item) for item in products]


def list_products_paginated(
    db: Session,
    page: int,
    size: int,
    search: str | None = None,
    min_preco: float | None = None,
    max_preco: float | None = None,
) -> dict:
    filters = []
    if search:
        pattern = f"%{search.strip().lower()}%"
        filters.append(func.lower(Product.nome).like(pattern))
    if min_preco is not None:
        filters.append(Product.preco >= float(min_preco))
    if max_preco is not None:
        filters.append(Product.preco <= float(max_preco))

    count_query = select(func.count(Product.id))
    data_query = select(Product)
    if filters:
        count_query = count_query.where(*filters)
        data_query = data_query.where(*filters)

    total = int(db.scalar(count_query) or 0)
    offset = (page - 1) * size

    items = db.scalars(
        data_query.order_by(Product.id.asc()).offset(offset).limit(size)
    ).all()

    pages = (total + size - 1) // size if total > 0 else 0
    return {
        "items": [product_payload(item) for item in items],
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }


def get_user_profile(db: Session, account: Account) -> dict:
    user = _get_user_for_account(db, account)
    return {
        "id": user.id,
        "nome": user.nome,
        "email": user.email,
        "saldo": _round_money(user.saldo),
    }


def recharge_balance(db: Session, account: Account, valor: float) -> dict:
    user = _get_user_for_account(db, account)
    user.saldo = _round_money(user.saldo + float(valor))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"saldo": _round_money(user.saldo)}


def checkout(db: Session, account: Account, produtos_ids: list[int]) -> dict:
    user = _get_user_for_account(db, account)

    unique_ids = sorted(set(int(item) for item in produtos_ids))
    products_lookup = {
        product.id: product
        for product in db.scalars(select(Product).where(Product.id.in_(unique_ids)))
    }

    valid_products: list[Product] = []
    invalid_ids: list[str] = []
    for raw_id in produtos_ids:
        product = products_lookup.get(int(raw_id))
        if product:
            valid_products.append(product)
        else:
            invalid_ids.append(str(raw_id))

    if invalid_ids:
        raise HTTPException(status_code=404, detail=f"Produto(s) invalido(s): {', '.join(invalid_ids)}.")

    total = _round_money(sum(float(item.preco) for item in valid_products))
    if float(user.saldo) < total:
        missing = _round_money(total - float(user.saldo))
        raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Faltam R$ {missing:.2f}.")

    user.saldo = _round_money(float(user.saldo) - total)
    order = Order(usuario_id=user.id, total=total, created_at=datetime.now(timezone.utc))
    db.add(order)
    db.flush()

    for product in valid_products:
        db.add(OrderItem(order_id=order.id, product_id=product.id))

    db.commit()

    reloaded_order = db.scalar(
        select(Order)
        .where(Order.id == order.id)
        .options(
            selectinload(Order.user),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
    )
    if not reloaded_order:
        raise HTTPException(status_code=500, detail="Falha ao carregar pedido criado.")

    return order_payload(reloaded_order)


def list_user_orders(db: Session, account: Account) -> list[dict]:
    user = _get_user_for_account(db, account)
    orders = db.scalars(
        select(Order)
        .where(Order.usuario_id == user.id)
        .order_by(Order.id.desc())
        .options(
            selectinload(Order.user),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
    ).all()
    return [order_payload(item) for item in orders]


def list_user_orders_paginated(db: Session, account: Account, page: int, size: int) -> dict:
    user = _get_user_for_account(db, account)

    total = int(db.scalar(select(func.count(Order.id)).where(Order.usuario_id == user.id)) or 0)
    offset = (page - 1) * size
    orders = db.scalars(
        select(Order)
        .where(Order.usuario_id == user.id)
        .order_by(Order.id.desc())
        .offset(offset)
        .limit(size)
        .options(
            selectinload(Order.user),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
    ).all()
    pages = (total + size - 1) // size if total > 0 else 0
    return {
        "items": [order_payload(item) for item in orders],
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }


def list_all_orders(db: Session) -> list[dict]:
    orders = db.scalars(
        select(Order)
        .order_by(Order.id.desc())
        .options(
            selectinload(Order.user),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
    ).all()
    return [order_payload(item) for item in orders]
