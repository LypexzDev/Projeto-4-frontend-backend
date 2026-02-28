from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_user_account
from app.db.models import Account
from app.db.session import get_db
from app.schemas.shop import CheckoutPayload, RecargaPayload
from app.services import shop_service

router = APIRouter(prefix="/shop", tags=["shop"])


@router.get("/produtos")
def shop_list_products(db: Session = Depends(get_db)):
    return shop_service.list_products(db)


@router.get("/me")
def shop_me(account: Account = Depends(get_user_account), db: Session = Depends(get_db)):
    return shop_service.get_user_profile(db, account)


@router.post("/recarga")
def shop_recharge(
    payload: RecargaPayload,
    account: Account = Depends(get_user_account),
    db: Session = Depends(get_db),
):
    return shop_service.recharge_balance(db, account, payload.valor)


@router.post("/pedidos")
def shop_checkout(
    payload: CheckoutPayload,
    account: Account = Depends(get_user_account),
    db: Session = Depends(get_db),
):
    return shop_service.checkout(db, account, payload.produtos_ids)


@router.get("/pedidos")
def shop_list_orders(account: Account = Depends(get_user_account), db: Session = Depends(get_db)):
    return shop_service.list_user_orders(db, account)

