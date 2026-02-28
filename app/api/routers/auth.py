from __future__ import annotations

from fastapi import APIRouter, Body, Cookie, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_account
from app.core.config import get_settings
from app.db.models import Account
from app.db.session import get_db
from app.schemas.auth import LoginPayload, RefreshTokenPayload, RegisterUserPayload
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.refresh_cookie_name, path="/auth")


@router.post("/register-user")
def register_user(payload: RegisterUserPayload, db: Session = Depends(get_db)):
    return auth_service.register_user(db, payload)


@router.post("/login-user")
def login_user(payload: LoginPayload, response: Response, db: Session = Depends(get_db)):
    result = auth_service.login_by_role(db, payload, role="user")
    _set_refresh_cookie(response, result["refresh_token"])
    result.pop("refresh_token", None)
    return result


@router.post("/login-admin")
def login_admin(payload: LoginPayload, response: Response, db: Session = Depends(get_db)):
    result = auth_service.login_by_role(db, payload, role="admin")
    _set_refresh_cookie(response, result["refresh_token"])
    result.pop("refresh_token", None)
    return result


@router.get("/me")
def auth_me(account: Account = Depends(get_current_account)):
    return {"account": auth_service.account_public_payload(account)}


@router.post("/logout")
def auth_logout(response: Response, account: Account = Depends(get_current_account), db: Session = Depends(get_db)):
    auth_service.logout_account(db, account)
    _clear_refresh_cookie(response)
    return {"ok": True}


@router.post("/refresh")
def auth_refresh(
    response: Response,
    payload: RefreshTokenPayload | None = Body(default=None),
    refresh_cookie: str | None = Cookie(default=None, alias=settings.refresh_cookie_name),
    db: Session = Depends(get_db),
):
    refresh_token = refresh_cookie or (payload.refresh_token if payload else None)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token ausente.")

    result = auth_service.refresh_session(db, refresh_token)
    _set_refresh_cookie(response, result["refresh_token"])
    result.pop("refresh_token", None)
    return result
