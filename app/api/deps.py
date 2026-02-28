from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.models import Account
from app.db.session import get_db
from app.services.auth_service import get_account_from_token


def extract_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente.")

    prefix, _, token = authorization.partition(" ")
    if prefix.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Formato de token invalido.")
    return token.strip()


def get_current_account(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(extract_token),
) -> Account:
    auth_payload = getattr(request.state, "auth_payload", None)
    if isinstance(auth_payload, dict):
        subject = auth_payload.get("sub")
        try:
            account_id = int(subject)
        except (TypeError, ValueError):
            account_id = None
        if account_id:
            account = db.get(Account, account_id)
            if account:
                return account

    return get_account_from_token(db, token)


def get_admin_account(account: Account = Depends(get_current_account)) -> Account:
    if account.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    return account


def get_user_account(account: Account = Depends(get_current_account)) -> Account:
    if account.role != "user":
        raise HTTPException(status_code=403, detail="Acesso restrito a usuarios.")
    if not account.usuario_id:
        raise HTTPException(status_code=400, detail="Conta sem perfil vinculado.")
    return account
