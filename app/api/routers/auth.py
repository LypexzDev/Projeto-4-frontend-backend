from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_account
from app.db.models import Account
from app.db.session import get_db
from app.schemas.auth import LoginPayload, RefreshTokenPayload, RegisterUserPayload
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
def auth_logout(account: Account = Depends(get_current_account), db: Session = Depends(get_db)):
    auth_service.logout_account(db, account)
    return {"ok": True}


@router.post("/refresh")
def auth_refresh(payload: RefreshTokenPayload, db: Session = Depends(get_db)):
    return auth_service.refresh_session(db, payload.refresh_token)
