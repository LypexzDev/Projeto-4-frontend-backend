from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import extract_token, get_current_account
from app.db.models import Account
from app.db.session import get_db
from app.schemas.auth import LoginPayload, RegisterUserPayload
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register-user")
def register_user(payload: RegisterUserPayload, db: Session = Depends(get_db)):
    return auth_service.register_user(db, payload)


@router.post("/login-user")
def login_user(payload: LoginPayload, db: Session = Depends(get_db)):
    return auth_service.login_by_role(db, payload, role="user")


@router.post("/login-admin")
def login_admin(payload: LoginPayload, db: Session = Depends(get_db)):
    return auth_service.login_by_role(db, payload, role="admin")


@router.get("/me")
def auth_me(account: Account = Depends(get_current_account)):
    return {"account": auth_service.account_public_payload(account)}


@router.post("/logout")
def auth_logout(_: str = Depends(extract_token)):
    return {"ok": True}

