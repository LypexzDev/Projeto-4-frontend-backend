from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_admin_account
from app.db.models import Account
from app.db.session import get_db
from app.schemas.admin import ProdutoCreatePayload, ProdutoUpdatePayload, SiteConfigPayload
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/resumo")
def admin_summary(_: Account = Depends(get_admin_account), db: Session = Depends(get_db)):
    return admin_service.get_summary(db)


@router.get("/usuarios")
def admin_list_users(_: Account = Depends(get_admin_account), db: Session = Depends(get_db)):
    return admin_service.list_users(db)


@router.get("/produtos")
def admin_list_products(_: Account = Depends(get_admin_account), db: Session = Depends(get_db)):
    return admin_service.list_products(db)


@router.post("/produtos")
def admin_create_product(
    payload: ProdutoCreatePayload,
    _: Account = Depends(get_admin_account),
    db: Session = Depends(get_db),
):
    return admin_service.create_product(db, payload)


@router.patch("/produtos/{produto_id}")
def admin_update_product(
    produto_id: int,
    payload: ProdutoUpdatePayload,
    _: Account = Depends(get_admin_account),
    db: Session = Depends(get_db),
):
    return admin_service.update_product(db, produto_id, payload)


@router.delete("/produtos/{produto_id}")
def admin_delete_product(
    produto_id: int,
    _: Account = Depends(get_admin_account),
    db: Session = Depends(get_db),
):
    return admin_service.delete_product(db, produto_id)


@router.get("/pedidos")
def admin_list_orders(_: Account = Depends(get_admin_account), db: Session = Depends(get_db)):
    return admin_service.list_orders(db)


@router.get("/site-config")
def admin_get_site_config(_: Account = Depends(get_admin_account), db: Session = Depends(get_db)):
    return admin_service.get_site_config(db)


@router.patch("/site-config")
def admin_update_site_config(
    payload: SiteConfigPayload,
    _: Account = Depends(get_admin_account),
    db: Session = Depends(get_db),
):
    return admin_service.update_site_config(db, payload)

